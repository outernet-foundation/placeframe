# ObserveThing: `ObservableListBase.GetInitializationOperations()` silently drops elements when a subscriber re-subscribes to the same source mid-init-replay

**Repo:** `github.com/outernet-foundation/ObserveThing` (`Assets/Package/Core`)
**Pinned hash at time of investigation:** `73edcd9962c83898b444f066e33357a68cbe8507`
**Affected file:** `Runtime/ObservableListBase.cs`
**Symptom severity:** silent — no exception, no log, just missing items downstream.
**Platform where observed:** Unity 6000.0.66f1, Android, IL2CPP.

---

## TL;DR

`ObservableListBase<T>` reuses a single mutable `List<ListOpArgs<T>> _initOps` field across calls to `GetInitializationOperations()`. The method `Clear()`s and refills this list each call, then returns the *same instance*. Subscribers iterate this list via `foreach` inside their `OnOperation` handler.

If the lambda invoked during one of those iterations re-subscribes to the same observable (anywhere in the cascade, however indirectly — e.g. via `ObservableIndexOf(item).Subscribe(...)`), `GetInitializationOperations` runs again and calls `_initOps.Clear()` on the list the outer `foreach` is still enumerating. On Unity / IL2CPP this *silently terminates* the outer enumeration after the current element instead of throwing `InvalidOperationException` — so every element past index 0 is dropped downstream with no error path.

**Fix:** return a fresh list per call. Remove the `_initOps` field.

```diff
 private List<(uint id, T value)> _list = new List<(uint id, T value)>();
 private CollectionIdProvider _idProvider;
-private List<ListOpArgs<T>> _initOps = new List<ListOpArgs<T>>();

 protected override IReadOnlyList<ListOpArgs<T>> GetInitializationOperations()
 {
-    _initOps.Clear();
+    var ops = new List<ListOpArgs<T>>(_list.Count);
     for (int i = 0; i < _list.Count; i++)
     {
         var op = _list[i];
-        _initOps.Add(new ListOpArgs<T>(op.id, i, op.value, false));
+        ops.Add(new ListOpArgs<T>(op.id, i, op.value, false));
     }
-    return _initOps;
+    return ops;
 }
```

We applied this in our local PackageCache, rebuilt the APK, and the bug is gone. Same pattern exists in `ObservableValueBase._initOperations` and should be fixed similarly — though the symptom there would be different (single-element list, so `Clear()` isn't called; only the contained value gets mutated mid-iteration).

---

## Reproduction

This pattern triggers it (paraphrased from our `TabbedMenu` UI helper):

```csharp
var source = Props.List("Capture", "Validate"); // ObservableList<string>, 2 items

// Subscribe via ObservableCreate, where the lambda re-subscribes to `source` itself.
source.ObservableCreate(item =>
{
    // ObservableIndexOf(item) builds a ValueOperator. Subscribing to it
    // (via Props.List(...) below) triggers IndexOfObservable.ctor, which
    // synchronously calls source.Subscribe — i.e. re-enters GetInitializationOperations.
    var itemIndex = source.ObservableIndexOf(item);

    return BuildSomething(new()
    {
        bindings = Props.List(itemIndex.Subscribe(_ => { /* ... */ }))
    });
});
```

Expected: `ObservableCreate`'s lambda fires twice (once per source item) → 2 children produced.
Actual: lambda fires once for `"Capture"` → 1 child. `"Validate"` is silently skipped.

If you remove the re-entrant `source.ObservableIndexOf(item).Subscribe(...)` from the lambda (or hoist it outside), both items are processed normally.

---

## Cascade trace

For an `IListObservable<T> source` with `_list = [A, B]`:

1. Downstream chain (e.g. `source.ObservableCreate(...)`) subscribes. This is the chain's first subscriber on `source`.
2. `Observable<T>.Subscribe(observer)` runs:
   - `_observers.Add(observerData)`
   - `observer.OnOperation(GetInitializationOperations())` — `GetInitializationOperations` clears `_initOps` and refills with `[op(A), op(B)]`, returns the shared `_initOps` reference.
3. The `IListObserver` wrapper in `Subscribe(IListObserver<T>)` iterates: `foreach (var op in ops) observer.OnAdd(...)`.
4. **Iteration 0 (A):** Cascades into the user lambda. Inside the lambda, building the resulting control triggers a *second* `source.Subscribe(...)` (via `IndexOfObservable.ctor`, which always synchronously subscribes to its source list in its constructor).
5. That re-entrant `Subscribe` runs `Observable<T>.Subscribe(observer2)` → `_observers.Add(observer2)` → `observer2.OnOperation(GetInitializationOperations())` → **`_initOps.Clear()` ← mutation of the list the outer foreach is iterating**.
6. The re-entrant `Subscribe`'s own foreach iterates the freshly-rebuilt `_initOps` and processes A and B in `IndexOfObservable.HandleAdd` (which just updates a private list inside the operator). It completes.
7. Cascade returns to the outer foreach. The outer `Enumerator`'s captured `_version` no longer matches `_initOps._version`. **The next `MoveNext()` would normally throw `InvalidOperationException` ("Collection was modified")** — on .NET / Mono / Editor, it does. On IL2CPP/Android we observed that it does not throw; the enumerator simply does not yield element B. No exception is raised, no log, no diagnostic.
8. The chain proceeds as if `source` only ever had one element.

We did not chase down whether IL2CPP's enumerator codegen elides the version check, whether the foreach is degenerating to `for (i; i<Count; i++)` based on an `IReadOnlyList<T>` interface analysis, or whether an exception is being swallowed at a layer we missed. Either way, the trigger — `_initOps.Clear()` mid-iteration of the same list — is independently a bug; the silent-failure mode is just a particularly nasty consequence.

---

## Empirical evidence

After adding granular logs around the user lambda inside `ObservableCreate`:

```
TabbedMenu props.tabs is ObservableList<string> count=2, items=[Capture,Validate]
TabbedMenu source.onAdd idx=0 label='Capture'      <- direct probe subscribe (no re-entry)
TabbedMenu source.onAdd idx=1 label='Validate'     <- direct probe subscribe (no re-entry)
TabbedMenu user lambda START tab='Capture'         <- ObservableCreate cascade, first item
TabbedMenu after ObservableIndexOf tab='Capture'
TabbedMenu before tabIndex.Subscribe tab='Capture'
TabbedMenu after tabIndex.Subscribe tab='Capture'
TabbedMenu user lambda END tab='Capture'           <- lambda completes cleanly for Capture
                                                    <- (no "START tab='Validate'" ever logged)
```

Observations:

- The source list has 2 items at subscribe time (confirmed by direct `.Count` and by the probe subscribe which receives both `onAdd` events).
- The `ObservableCreate` lambda's first invocation runs to completion (all 5 logs fire) — including the `tabIndex.Subscribe` re-entry point.
- The `ObservableCreate` lambda's second invocation never starts.
- No exception is logged anywhere: not in Unity `Debug.LogException` (the default `Settings.DefaultExceptionHandler` route), not in our project's Serilog/Loki sink, not in `Application.logMessageReceived`, not in Android logcat. A wide `grep` of logcat at the relevant timestamp for `InvalidOperation|Collection.*modified|Enumeration` returned zero hits.
- After applying the fix above (returning a fresh `List<ListOpArgs<T>>` from `GetInitializationOperations`), the lambda fires for both `'Capture'` and `'Validate'` and the UI renders both tabs. The fix takes effect with no other changes.

---

## Why it's easy to introduce this pattern accidentally

The re-entry doesn't have to be syntactically obvious. In our case it goes:

```
ObservableCreate lambda
  └─ ObservableIndexOf(label).Subscribe(...)            // user-facing API
       └─ ValueOperator.OnFirstObserverAdded             // ObserveThing internal
            └─ new IndexOfObservable(source, ...)        // ObserveThing internal
                 └─ source.Subscribe(...)                // ← here: re-entrant subscribe
                      └─ source.GetInitializationOperations()
                           └─ _initOps.Clear()           // ← mutates outer foreach's list
```

Any operator that takes an `IListObservable<T>` and subscribes to it in its constructor will reproduce this when used inside `source.ObservableCreate(item => ...)` (or any other `IListObservable` operator chain) on the same source. `IndexOfObservable` is one example; any future operator with the same constructor shape would also trigger it.

---

## Related: `ObservableValueBase._initOperations`

`Runtime/ObservableValueBase.cs` has the same shared-mutable-state pattern:

```csharp
private List<T> _initOperations = new List<T>();
public ObservableValueBase(ObservationContext context, T value) : base(context)
{
    _value = value;
    _initOperations.Add(default);
}
protected override IReadOnlyList<T> GetInitializationOperations()
{
    _initOperations[0] = _value;
    return _initOperations;
}
```

The list is always size 1, so `Clear()` isn't called — but the single element is mutated in place. Re-entrant `GetInitializationOperations` calls would mutate the list a subscriber is currently reading. We did not observe a concrete bug from this in our app, but the fix is the same (return `new[] { _value }` or `new List<T> { _value }`) and removes the foot-gun.

---

## Suggested test

A regression test that exercises the pattern:

```csharp
[Test]
public void ObservableCreate_with_reentrant_subscribe_in_lambda_emits_all_items()
{
    var source = new ObservableList<int>(1, 2, 3);

    var seen = new List<int>();
    source
        .ObservableCreate(x =>
        {
            // Re-subscribe to the same source from within the lambda.
            // (ObservableIndexOf does this synchronously via IndexOfObservable.ctor.)
            var _ = source.ObservableIndexOf(x).Subscribe(idx => { });
            seen.Add(x);
            return new SomeIControl();   // replace with whatever satisfies the U: IControl bound
        })
        .Subscribe(onAdd: (_, _) => { });

    Assert.AreEqual(new[] { 1, 2, 3 }, seen);
}
```

Prior to the fix this fails with `seen == [1]` (no exception). After the fix, it passes.

---

## Notes

- We did not investigate why IL2CPP doesn't throw `InvalidOperationException` here. Reproducing the same bug in Editor (Mono) would presumably surface the exception via the default exception handler, which would have made this much easier to diagnose. Worth a sanity check on the maintainer's end.
- The application-side workaround (avoid re-subscribing inside `ObservableCreate` lambdas, or hoist subscriptions outside) is straightforward but only addresses one call site. Fixing it in the library covers everyone.

---

## Issue #2: `ObservableWithPrevious<T>` tuple ordering (usability, not correctness)

This isn't a correctness bug in the library — but it's a foot-gun that bit us alongside the above, and is worth raising while you're touching the package.

`Runtime/Operators/Observables/WithPreviousObservable.cs` declares its emitted tuple as:

```csharp
public static IValueObservable<(T current, T previous)> ObservableWithPrevious<T>(this IValueObservable<T> source, ObservationContext context = default)
```

i.e. `(current, previous)` — current first. This is the inverse of the conventional ordering used by Rx.NET (e.g. `Buffer(2, 1).Select(pair => (pair[0], pair[1]))`), most MVU helpers, and the C# `event` pattern (`(sender, OldValue, NewValue)`). C# tuple destructuring is positional, not by name. Callers naturally write `(previous, current) => ...` because that's the convention everywhere else, the compiler binds positionally, and their `previous` parameter receives the *current* value (and vice versa). The names appear correct in source review because they read in conventional order — the bug is invisible at the call site.

This was a real bug in our project: the caller's `RemoveLocalizationMap(previous)` ended up removing the just-selected map (which had never been added), and `AddLocalizationMap(current)` early-returned on `Guid.Empty`. The exception was logged but the user-visible symptom — "localization never starts" — wasn't obviously connected.

### Why we think this should be flipped in the library, not just documented

Specifically because of LLM coding agents.

Claude Code (the agent that drove this bug investigation and wrote this report) initially wrote the call site this way by convention. Even with the source of `WithPreviousObservable.cs` directly accessible and grep-able, the natural completion pattern for `something.ObservableWithPrevious().Subscribe(($1, $2) => ...)` defaults to `(previous, current)` because that's the strongest prior in training data across Rx.NET, RxJS, MVU patterns, the `INotifyPropertyChanged` `(OldValue, NewValue)` convention, etc. A doc-comment like `// emits (current, previous) — note the order` is mostly ignored at completion time; the training-data prior is much stronger than a single inline comment.

Human developers can absorb "oh, this one's flipped, I'll just remember" once and write correct code thereafter. Agents can't — every new completion starts fresh, the prior re-fires, and the only durable fix is for the API itself to match the prior. This is a real and growing category of API-design concern as agent-driven coding becomes the default; APIs that "fight the prior" generate silent bugs at scale.

### Suggested fix

Rename the tuple to `(T previous, T current)`. This is a breaking change for callers who relied on named-tuple access (`.current` / `.previous`), but those callers will get a compile error, which is the desirable failure mode. Callers using positional destructuring (`(a, b) => ...`) won't notice the rename at the type level — but if they were using the agent-driven `(previous, current)` convention, they'll now be correct by default rather than incorrect by default.

If a non-breaking change is preferred, a deprecated alias is straightforward:

```csharp
[Obsolete("Use ObservableWithPrevious which emits (previous, current). The legacy (current, previous) order was unconventional.")]
public static IValueObservable<(T current, T previous)> ObservableWithPreviousLegacy<T>(...) => ...;

public static IValueObservable<(T previous, T current)> ObservableWithPrevious<T>(...) => ...;
```

Either way: don't leave the current order in place and rely on doc-comments. The current order is itself the foot-gun.
