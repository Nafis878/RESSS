"""Exploratory outer-group sensitivity, separate from primary asset inference."""
import pandas as pd
from scipy.stats import binomtest
from method_validation.run import OUT, holm


def main():
    x = pd.read_csv(OUT / 'paired_asset_contrasts.csv', dtype={'unit': str, 'split': str})
    s = x.groupby(['dataset', 'analysis', 'contrast', 'split']).value.agg(['mean', 'size']).reset_index()
    s.to_csv(OUT / 'outer_group_contrasts.csv', index=False)
    rows = []
    for (ds, an, contrast), g in s.groupby(['dataset', 'analysis', 'contrast']):
        pos = int((g['mean'] > 1e-12).sum())
        neg = int((g['mean'] < -1e-12).sum())
        total = pos + neg
        rows.append(dict(dataset=ds, analysis=an, contrast=contrast,
                         primary_regime=not (ds == 'Battery' and an == 'cv123'),
                         outer_groups=len(g), positive=pos, negative=neg,
                         ties=len(g) - total, p_raw=binomtest(pos, total, .5).pvalue if total else 1.,
                         interpretation='exploratory; assumes independent fair signs of outer-group means'))
    q = pd.DataFrame(rows)
    for flag in [True, False]:
        mask = q.primary_regime == flag
        q.loc[mask, 'p_holm'] = holm(q.loc[mask, 'p_raw'])
    q.to_csv(OUT / 'outer_group_sign_sensitivity.csv', index=False)
    print(q[['dataset', 'analysis', 'contrast', 'outer_groups', 'p_raw', 'p_holm']].to_string(index=False))


if __name__ == '__main__':
    main()
