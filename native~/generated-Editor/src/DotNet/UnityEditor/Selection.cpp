#include <DotNet/UnityEditor/Selection.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEditor {

Selection::Selection(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Selection::Selection(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Selection::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Selection::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Selection::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Selection::GetHandle() {
    return this->_handle;
}


Selection::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEditor::Selection::Property_get_activeGameObject)(void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject Selection::activeGameObject() {
    void* reinteropException = nullptr;
    auto result = Property_get_activeGameObject(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEditor::Selection::Property_set_activeGameObject)(void* value, void** reinteropException) = nullptr;


void Selection::activeGameObject(const ::DotNet::UnityEngine::GameObject& value) {
    void* reinteropException = nullptr;
    Property_set_activeGameObject(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEditor


