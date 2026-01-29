// using R3;
// using UnityEditor;
// using UnityEditor.Compilation;
// using UnityEngine;
// using System;
// using System.Collections.Generic;

// [InitializeOnLoad]
// public class ExitPlaymodeOnScriptReload
// {
//     static DateTime? lockTime = null;

//     static ExitPlaymodeOnScriptReload()
//     {
//         ObservableTracker.EnableTracking = true;
//         ObservableTracker.EnableStackTrace = true;

//         CompilationPipeline.compilationStarted += (_) =>
//         {
//             lockTime = DateTime.Now;
//             EditorApplication.LockReloadAssemblies();
//             EditorApplication.ExitPlaymode();
//         };

//         EditorApplication.update += () =>
//         {
//             if (!lockTime.HasValue) return;

//             List<string> activeTasks = new List<string>();
//             ObservableTracker.ForEachActiveTask(task => activeTasks.Add(task.StackTrace));
//             Debug.Log($"Waiting for {activeTasks.Count} active tasks to complete before unlocking assembly reload");

//             if (activeTasks.Count == 0 || DateTime.Now - lockTime.Value > TimeSpan.FromSeconds(3))
//             {
//                 if (activeTasks.Count > 0)
//                 {
//                     Debug.LogError("Timeout reached. Unlocking assembly reload with active tasks remaining:\n\n" + string.Join("\n\n", activeTasks));
//                 }

//                 lockTime = null;
//                 EditorApplication.UnlockReloadAssemblies();
//             }
//         };
//     }
// }