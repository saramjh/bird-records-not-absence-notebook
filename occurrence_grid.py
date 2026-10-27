from collections import Counter
from math import floor, isfinite

def screen(records, threshold=1000):
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    accepted, excluded, seen = [], Counter(), set()
    for r in records:
        rid = str(r.get("gbifID") or "")
        if not rid or rid in seen:
            excluded["missing_or_duplicate_id"] += 1
            continue
        seen.add(rid)
        if "creativecommons.org/publicdomain/zero/1.0" not in str(r.get("license") or "").lower():
            excluded["not_cc0"] += 1
            continue
        if r.get("countryCode") != "KR" or r.get("basisOfRecord") != "HUMAN_OBSERVATION" or r.get("year") not in (2024, "2024"):
            excluded["outside_scope"] += 1
            continue
        try:
            lat, lon = float(r["decimalLatitude"]), float(r["decimalLongitude"])
            if not(isfinite(lat) and isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
                raise ValueError("out of range")
        except (KeyError, TypeError, ValueError):
            excluded["invalid_coordinate"] += 1
            continue
        unc=r.get("coordinateUncertaintyInMeters")
        if unc is None:
            excluded["uncertainty_missing"] += 1
            continue
        try:
            unc=float(unc)
            if not isfinite(unc) or unc<0:
                raise ValueError("invalid")
        except (TypeError, ValueError):
            excluded["uncertainty_invalid"] += 1
            continue
        if unc>threshold:
            excluded["above_illustrative_threshold"] += 1
            continue
        accepted.append({"id":rid,"lat":lat,"lon":lon,"datasetKey":str(r.get("datasetKey") or "")})
    return accepted,dict(excluded)

def aggregate(points,meters):
    if meters<=0:
        raise ValueError("grid size must be positive")
    counts=Counter()
    for x,y in points:
        if not (isfinite(x) and isfinite(y)):
            raise ValueError("invalid projected position")
        counts[(floor(x/meters),floor(y/meters))]+=1
    return dict(counts)
