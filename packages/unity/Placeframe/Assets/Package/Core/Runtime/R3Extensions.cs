using R3;

public static class R3Extensions
{
    // This overload specifically handles Nullable<struct>
    public static Observable<T> WhereNotNull<T>(this Observable<T?> source)
        where T : struct
    {
        return source.Where(x => x.HasValue).Select(x => x.Value);
    }
}
