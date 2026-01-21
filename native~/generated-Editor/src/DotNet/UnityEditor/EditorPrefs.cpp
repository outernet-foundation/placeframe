#include <DotNet/UnityEditor/EditorPrefs.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>



namespace DotNet::UnityEditor {

EditorPrefs::EditorPrefs(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


EditorPrefs::EditorPrefs(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool EditorPrefs::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool EditorPrefs::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& EditorPrefs::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& EditorPrefs::GetHandle() {
    return this->_handle;
}


EditorPrefs::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::UnityEditor::EditorPrefs::CallHasKey_4Oa4KGDR__vvaosUsC29xLg)(void* key, void** reinteropException) = nullptr;


bool EditorPrefs::HasKey(const ::DotNet::System::String& key) {
    void* reinteropException = nullptr;
    auto result = CallHasKey_4Oa4KGDR__vvaosUsC29xLg(key.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*DotNet::UnityEditor::EditorPrefs::CallGetString_4Oa4KGDR__vvaosUsC29xLg)(void* key, void** reinteropException) = nullptr;


::DotNet::System::String EditorPrefs::GetString(const ::DotNet::System::String& key) {
    void* reinteropException = nullptr;
    auto result = CallGetString_4Oa4KGDR__vvaosUsC29xLg(key.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::EditorPrefs::CallSetString_eMSjpsyKrCDpoy__674Qaew)(void* key, void* value, void** reinteropException) = nullptr;


void EditorPrefs::SetString(const ::DotNet::System::String& key, const ::DotNet::System::String& value) {
    void* reinteropException = nullptr;
    CallSetString_eMSjpsyKrCDpoy__674Qaew(key.GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEditor::EditorPrefs::CallDeleteKey_4Oa4KGDR__vvaosUsC29xLg)(void* key, void** reinteropException) = nullptr;


void EditorPrefs::DeleteKey(const ::DotNet::System::String& key) {
    void* reinteropException = nullptr;
    CallDeleteKey_4Oa4KGDR__vvaosUsC29xLg(key.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEditor


