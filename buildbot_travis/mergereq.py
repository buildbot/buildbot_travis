
def mergeRequests(builder, req1, req2):
    if not req1.source.canBeMergedWith(req2.source):
       return False

    props1 = set((k,v1) for (k, v1, v2) in req1.properties.asList() if v2 == ".travis.yml")
    props2 = set((k,v1) for (k, v1, v2) in req2.properties.asList() if v2 == ".travis.yml")

    if len(props1 - props2) > 0 or len(props2 - props1) > 0:
        return False

    return True

