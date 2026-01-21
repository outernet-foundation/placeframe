#include <DotNet/UnityEditor/EditorApplication.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEditor/CallbackFunction.h>



namespace DotNet::UnityEditor {

EditorApplication::EditorApplication(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


EditorApplication::EditorApplication(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool EditorApplication::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool EditorApplication::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& EditorApplication::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& EditorApplication::GetHandle() {
    return this->_handle;
}


EditorApplication::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::UnityEditor::EditorApplication::Property_get_isPlaying)(void** reinteropException) = nullptr;


bool EditorApplication::isPlaying() {
    void* reinteropException = nullptr;
    auto result = Property_get_isPlaying(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::UnityEditor::EditorApplication::Property_set_isPlaying)(::std::uint8_t value, void** reinteropException) = nullptr;


void EditorApplication::isPlaying(bool value) {
    void* reinteropException = nullptr;
    Property_set_isPlaying(value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEditor::EditorApplication::CallExecuteMenuItem__mTAWffFaNJNxtE3VLYhxw)(void* menuItemPath, void** reinteropException) = nullptr;


bool EditorApplication::ExecuteMenuItem(const ::DotNet::System::String& menuItemPath) {
    void* reinteropException = nullptr;
    auto result = CallExecuteMenuItem__mTAWffFaNJNxtE3VLYhxw(menuItemPath.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*DotNet::UnityEditor::EditorApplication::Field_get_update)(void** reinteropException) = nullptr;


void (*DotNet::UnityEditor::EditorApplication::Field_set_update)(void* value, void** reinteropException) = nullptr;


::DotNet::UnityEditor::CallbackFunction EditorApplication::update() {
    void* reinteropException = nullptr;
    auto result = Field_get_update(&reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::UnityEditor::CallbackFunction(::DotNet::Reinterop::ObjectHandle(result));
}


void EditorApplication::update(const ::DotNet::UnityEditor::CallbackFunction& value) {
    void* reinteropException = nullptr;
    Field_set_update(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


} // namespace DotNet::UnityEditor


