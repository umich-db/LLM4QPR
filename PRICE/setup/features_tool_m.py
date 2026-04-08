"""
PRICE_M: Extended PRICE feature extractor supporting IN and LIKE predicates.

Filter encoding: 61 dims = histogram(40) + 10 ranges(20) + selectivity(1)

For discrete (categorical) filter columns:
- histogram(40): SpaceSaving values / table_size (same as PRICE)
- 10 ranges(20):
    - First 9 ranges (18 dims): [idx/bin_size, (idx+1)/bin_size] for top-9
      most frequent matched values, sorted by frequency descending
    - Last range (2 dims): [min(remaining_idx)/bin_size, (max(remaining_idx)+1)/bin_size]
      as catchall for remaining matched values
    - Unmatched range slots: [0, 0]
- selectivity(1): sum of all matched value frequencies / table_size

For continuous filter columns:
- histogram(40): bin histogram / table_size (same as PRICE)
- 10 ranges(20): first range slot = [norm_min, norm_max], rest = [0, 0]
- selectivity(1): histogram-based selectivity (same as PRICE)
"""

import re
import numpy as np
import torch
import sqlglot

from setup.features_tool import Sql2Feature


class Sql2FeatureM(Sql2Feature):
    """Extended PRICE feature extractor with multi-value (IN, LIKE) support.

    filter_dim = bin_size + 21 = 61 (for bin_size=40)
    """

    NUM_RANGES = 10  # 9 individual + 1 catchall

    @property
    def filter_dim_m(self):
        """PRICE_M filter dimension: bin_size + 20 (ranges) + 1 (selectivity)."""
        return self.bin_size + self.NUM_RANGES * 2 + 1

    def _like_to_in_values(self, pattern, keys):
        """Convert a LIKE pattern to a list of matching SpaceSaving keys.

        Args:
            pattern: SQL LIKE pattern string (e.g., "'%Drama%'" with quotes)
            keys: SpaceSaving keys list (last entry is 'OtHeRs' or padding)

        Returns:
            List of matching key values (excluding 'OtHeRs' and padding).
        """
        # Strip surrounding quotes
        p = pattern.strip("'\"")
        # Convert SQL LIKE pattern to regex:
        # Split on % (any-sequence wildcard), escape literal parts, rejoin with .*
        # Also convert _ (single-char wildcard) to .
        parts = p.split('%')
        regex_parts = [re.escape(part).replace('_', '.') for part in parts]
        regex_str = '.*'.join(regex_parts)
        regex = re.compile(f'^{regex_str}$', re.IGNORECASE)

        matched = []
        for key in keys:
            if key == 'OtHeRs' or key == -1e3:
                continue
            if isinstance(key, str) and regex.match(key):
                matched.append(key)
        return matched

    @staticmethod
    def _unquoted_col_ref(node):
        """Return unquoted 'table.column' string from a sqlglot Column node."""
        if hasattr(node, 'table') and node.table:
            return f"{node.table}.{node.name}"
        return str(node)

    def _get_filter_type_from_sql(self, sql, column):
        """Detect filter type and values for a column from parsed SQL.

        Returns:
            ('eq', value)           for single equality
            ('in', [values])        for IN list
            ('not_like', pattern)   for NOT LIKE / NOT ILIKE
            ('like', pattern_str)   for LIKE / ILIKE
            None                    if no recognized filter found
        """
        parsed_sql = sqlglot.parse_one(sql)
        where = parsed_sql.args.get("where")
        if where is None:
            return None

        # Priority: IN > NOT LIKE > LIKE > EQ
        for in_node in where.find_all(sqlglot.exp.In):
            if column == self._unquoted_col_ref(in_node.this):
                values = in_node.expressions
                if values:
                    parsed_vals = []
                    for v in values:
                        try:
                            parsed_vals.append(int(str(v)))
                        except ValueError:
                            try:
                                parsed_vals.append(float(str(v)))
                            except ValueError:
                                parsed_vals.append(str(v).replace("'", ""))
                    return ('in', parsed_vals)

        # NOT LIKE / NOT ILIKE (check before bare LIKE since Not wraps Like)
        for not_node in where.find_all(sqlglot.exp.Not):
            child = not_node.this
            if isinstance(child, (sqlglot.exp.Like, sqlglot.exp.ILike)):
                if column == self._unquoted_col_ref(child.this):
                    pattern = str(child.expression)
                    return ('not_like', pattern)

        for like_type in (sqlglot.exp.Like, sqlglot.exp.ILike):
            for like_node in where.find_all(like_type):
                if column == self._unquoted_col_ref(like_node.this):
                    pattern = str(like_node.expression)
                    return ('like', pattern)

        for eq_node in where.find_all(sqlglot.exp.EQ):
            if column != self._unquoted_col_ref(eq_node.args["this"]):
                continue
            if isinstance(eq_node.args["expression"], sqlglot.exp.Column):
                continue  # join condition, not filter
            try:
                val = int(str(eq_node.args["expression"]))
            except ValueError:
                try:
                    val = float(str(eq_node.args["expression"]))
                except ValueError:
                    val = str(eq_node.args["expression"]).replace("'", "")
            return ('eq', val)

        return None

    def _encode_multi_ranges(self, matched_values, keys, values):
        """Encode matched values into 10 ranges (20 dims).

        First 9 ranges: top-9 most frequent matched values
            Each as [idx/bin_size, (idx+1)/bin_size]
        Last range: catchall [min(remaining)/bin_size, (max(remaining)+1)/bin_size]

        Args:
            matched_values: list of values to look up in SpaceSaving
            keys: SpaceSaving keys (list, last is 'OtHeRs')
            values: SpaceSaving frequencies (list, same length as keys)

        Returns:
            (ranges_tensor[20], total_frequency)
        """
        if not matched_values:
            return torch.zeros(self.NUM_RANGES * 2), 0.0

        # Find index and frequency for each matched value
        matched_info = []  # [(key_index, frequency), ...]
        for val in matched_values:
            try:
                idx = keys.index(val)
                freq = values[idx]
            except ValueError:
                # Value not in top-(bin_size-1), falls into OtHeRs bucket
                idx = len(keys) - 1
                freq = values[-1]
            matched_info.append((idx, freq))

        # Sort by frequency descending (most frequent first)
        matched_info.sort(key=lambda x: x[1], reverse=True)

        ranges = torch.zeros(self.NUM_RANGES * 2)
        total_freq = 0.0

        # First 9 ranges: top-9 most frequent matched values
        n_individual = min(self.NUM_RANGES - 1, len(matched_info))
        for i in range(n_individual):
            idx, freq = matched_info[i]
            ranges[2 * i] = idx / self.bin_size
            ranges[2 * i + 1] = (idx + 1) / self.bin_size
            total_freq += freq

        # Last range: catchall for remaining matched values
        if len(matched_info) > self.NUM_RANGES - 1:
            remaining = matched_info[self.NUM_RANGES - 1:]
            remaining_indices = [info[0] for info in remaining]
            last = self.NUM_RANGES - 1
            ranges[2 * last] = min(remaining_indices) / self.bin_size
            ranges[2 * last + 1] = (max(remaining_indices) + 1) / self.bin_size
            total_freq += sum(info[1] for info in remaining)

        return ranges, total_freq

    def create_sql_features(self, sql):
        """Create SQL features with PRICE_M encoding (61-dim filters).

        Same structure as PRICE but with extended filter encoding:
        - Supports IN (multiple value selection)
        - Supports LIKE (pattern matching via SpaceSaving key lookup)
        - Uses 10 ranges (20 dims) instead of 1 range (2 dims)
        """
        columns, tables, joins, ref_to_tables = self.parse_sql(sql)

        # Single-table queries: no join constraint needed
        if len(tables) > 1:
            if len(tables) != len(joins) + 1:
                print(f"error: {sql}")
                return None
            assert len(tables) == len(joins) + 1

        table_join_cols_dict, table_filter_cols_dict = {}, {}
        for table in tables:
            table_join_cols_dict[table] = []
            table_filter_cols_dict[table] = []

        for column in columns:
            table = column.split(".")[0]
            join_flag = False
            for join in joins:
                left_join_col = join.split("=")[0].strip()
                right_join_col = join.split("=")[1].strip()
                if column == left_join_col or column == right_join_col:
                    join_flag = True
                    break
            if join_flag:
                table_join_cols_dict[table].append(column)
            else:
                table_filter_cols_dict[table].append(column)

        join_columns = self.flatten_list(list(table_join_cols_dict.values()))
        filter_columns = self.flatten_list(list(table_filter_cols_dict.values()))

        table_features = []
        table_sels = {}
        for table in tables:
            table_sels[table] = []

        # Join column histograms (same as PRICE)
        join_column_histograms = []
        for join_column in join_columns:
            join_column_histogram = self.get_column_histograms(join_column)
            join_column_histograms.append(torch.tensor(join_column_histogram))

        # Fanout features (same as PRICE)
        fanout_features = []
        for join in joins:
            ff1, ff2 = self.get_fanout_features(join)
            fanout_features.append(torch.tensor(ff1))
            fanout_features.append(torch.tensor(ff2))

        # PRICE_M filter encoding
        fdim = self.filter_dim_m
        filter_column_features = []

        for filter_column in filter_columns:
            col_name = filter_column.split('.')[-1]
            col_table = filter_column.split('.')[0]
            is_discrete = col_name in self.information_coltype['col_type'][col_table]['dsct']

            if is_discrete:
                keys, vals = self.space_saving_summary(filter_column)
                table_size = self.get_table_size(col_table)
                histogram = torch.tensor(vals) / table_size

                filter_info = self._get_filter_type_from_sql(sql, filter_column)

                if filter_info is not None:
                    ftype, fval = filter_info

                    if ftype == 'eq':
                        ranges, total_freq = self._encode_multi_ranges([fval], keys, vals)
                        selectivity = total_freq / table_size

                    elif ftype == 'in':
                        ranges, total_freq = self._encode_multi_ranges(fval, keys, vals)
                        selectivity = total_freq / table_size

                    elif ftype == 'like':
                        matched = self._like_to_in_values(fval, keys)
                        if matched:
                            ranges, total_freq = self._encode_multi_ranges(matched, keys, vals)
                            selectivity = total_freq / table_size
                        else:
                            # No match in top-39 keys; attribute to OtHeRs
                            ranges = torch.zeros(self.NUM_RANGES * 2)
                            others_idx = len(keys) - 1
                            ranges[0] = others_idx / self.bin_size
                            ranges[1] = (others_idx + 1) / self.bin_size
                            selectivity = vals[-1] / table_size

                    elif ftype == 'not_like':
                        # NOT LIKE: match pattern, then take complement
                        matched = self._like_to_in_values(fval, keys)
                        matched_set = set(matched)
                        # Unmatched = all real keys (excluding OtHeRs/padding) minus matched
                        unmatched = [k for k in keys
                                     if k != 'OtHeRs' and k != -1e3 and k not in matched_set]
                        if unmatched:
                            ranges, total_freq = self._encode_multi_ranges(unmatched, keys, vals)
                            selectivity = total_freq / table_size
                        else:
                            # Everything matched → NOT LIKE selects nothing from top-39
                            # Only OtHeRs values remain
                            ranges = torch.zeros(self.NUM_RANGES * 2)
                            others_idx = len(keys) - 1
                            ranges[0] = others_idx / self.bin_size
                            ranges[1] = (others_idx + 1) / self.bin_size
                            selectivity = vals[-1] / table_size

                    if selectivity == 0.0:
                        selectivity = 1e-6

                    sel_tensor = torch.tensor([selectivity])
                    table_sels[col_table].append(selectivity)
                    feature = torch.cat([histogram, ranges, sel_tensor])

                else:
                    # Discrete column with non-EQ/IN/LIKE filter (e.g., <, >)
                    # Fall back to histogram-based encoding with zero-padded ranges
                    histogram = torch.tensor(self.get_column_histograms(filter_column))
                    ranges = torch.zeros(self.NUM_RANGES * 2)
                    norm_range = self.get_filter_norm_range(
                        sql, filter_column, self.columns_bin_edges[filter_column])
                    ranges[0] = norm_range[0]
                    ranges[1] = norm_range[1]
                    range_low, range_high = self.get_filter_ranges(sql, filter_column)
                    distribution = self.columns_distributions[filter_column]
                    bin_edges = self.columns_bin_edges[filter_column]
                    selectivity = self.calculate_hist_selectivity(
                        distribution, bin_edges, range_low, range_high
                    ) / self.get_table_size(col_table)
                    if selectivity == 0.0:
                        selectivity = 1e-6
                    sel_tensor = torch.tensor([selectivity])
                    table_sels[col_table].append(selectivity)
                    feature = torch.cat([histogram, ranges, sel_tensor])

            else:
                # Continuous column: histogram + ranges (first slot only) + selectivity
                histogram = torch.tensor(self.get_column_histograms(filter_column))
                ranges = torch.zeros(self.NUM_RANGES * 2)
                norm_range = self.get_filter_norm_range(
                    sql, filter_column, self.columns_bin_edges[filter_column])
                ranges[0] = norm_range[0]
                ranges[1] = norm_range[1]
                range_low, range_high = self.get_filter_ranges(sql, filter_column)
                distribution = self.columns_distributions[filter_column]
                bin_edges = self.columns_bin_edges[filter_column]
                selectivity = self.calculate_hist_selectivity(
                    distribution, bin_edges, range_low, range_high
                ) / self.get_table_size(col_table)
                if selectivity == 0.0:
                    selectivity = 1e-6
                sel_tensor = torch.tensor([selectivity])
                table_sels[col_table].append(selectivity)
                feature = torch.cat([histogram, ranges, sel_tensor])

            assert feature.shape[0] == fdim, \
                f"Expected {fdim}-dim filter feature, got {feature.shape[0]}"
            filter_column_features.append(feature)

        # Table features: log_size, avi, minsel, ebo (same as PRICE)
        for table in tables:
            if len(table_sels[table]) == 0:
                avi = torch.tensor([1])
                minsel = torch.tensor([1])
                ebo = torch.tensor([1])
            else:
                avi = torch.prod(torch.tensor(table_sels[table]))
                minsel = torch.min(torch.tensor(table_sels[table]))
                sorted_sels = sorted(table_sels[table], reverse=True)
                ebo = 1
                for i in range(len(sorted_sels)):
                    if i > 3:
                        break
                    ebo = ebo * sorted_sels[i] ** (1 / (2 ** i))
                ebo = torch.tensor([ebo])
            table_size = self.get_table_size(table)
            _EPS = 1e-6
            if avi.item() == 0.0:
                avi = torch.tensor([_EPS])
            if minsel.item() == 0.0:
                minsel = torch.tensor([_EPS])
            if ebo.item() == 0.0:
                ebo = torch.tensor([_EPS])
            table_features.append(torch.cat([
                torch.tensor([np.log(table_size)]),
                torch.tensor([avi]),
                torch.tensor([minsel]),
                torch.tensor([ebo])
            ]))

        # Handle single-table queries (no joins/fanout)
        if len(join_columns) == 0:
            join_hist = torch.zeros(self.bin_size)
            fanout_feat = torch.zeros(self.bin_size * 2)
            n_jc = 1
            n_fo = 2
        else:
            join_hist = torch.cat(join_column_histograms)
            fanout_feat = torch.cat(fanout_features)
            n_jc = len(join_columns)
            n_fo = len(joins) * 2

        if len(filter_column_features) > 0:
            filter_feat = torch.cat(filter_column_features)
        else:
            filter_feat = torch.zeros(fdim)

        n_tb = len(tables)
        n_fc = max(len(filter_columns), 1) if len(filter_columns) == 0 else len(filter_columns)

        tensor_list = [join_hist, fanout_feat, torch.cat(table_features), filter_feat]
        sql_feature_len = len(torch.cat(tensor_list))

        sql_features = (join_hist, fanout_feat, torch.cat(table_features), filter_feat)

        expected = self.bin_size * (n_jc + n_fo) + 4 * n_tb + fdim * max(len(filter_columns), 1)
        assert sql_feature_len == expected, \
            f"Expected feature length {expected}, got {sql_feature_len}"

        if len(join_columns) > 0:
            assert len(join_columns) >= len(tables)
            assert len(joins) == len(tables) - 1

        return sql_features, n_jc, n_fo, n_tb, max(len(filter_columns), 1)
