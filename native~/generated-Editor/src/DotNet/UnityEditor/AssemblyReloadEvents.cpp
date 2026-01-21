#include <DotNet/UnityEditor/AssemblyReloadEvents.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEditor/AssemblyReloadCallback.h>



namespace DotNet::UnityEditor {

void (*DotNet::UnityEditor::AssemblyReloadEvents::Calladd_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException) = nullptr;


void AssemblyReloadEvents::add_afterAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value) {
    void* reinteropException = nullptr;
    Calladd_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEditor::AssemblyReloadEvents::Callremove_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException) = nullptr;


void AssemblyReloadEvents::remove_afterAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value) {
    void* reinteropException = nullptr;
    Callremove_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEditor::AssemblyReloadEvents::Calladd_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException) = nullptr;


void AssemblyReloadEvents::add_beforeAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value) {
    void* reinteropException = nullptr;
    Calladd_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEditor::AssemblyReloadEvents::Callremove_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException) = nullptr;


void AssemblyReloadEvents::remove_beforeAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value) {
    void* reinteropException = nullptr;
    Callremove_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEditor


