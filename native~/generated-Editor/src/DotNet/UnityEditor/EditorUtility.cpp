#include <DotNet/UnityEditor/EditorUtility.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Object.h>



namespace DotNet::UnityEditor {

EditorUtility::EditorUtility(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


EditorUtility::EditorUtility(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool EditorUtility::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool EditorUtility::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& EditorUtility::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& EditorUtility::GetHandle() {
    return this->_handle;
}


EditorUtility::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEditor::EditorUtility::CallSetDirty_byPIQUdz9akDU2__zoHd1tg)(void* target, void** reinteropException) = nullptr;


void EditorUtility::SetDirty(const ::DotNet::UnityEngine::Object& target) {
    void* reinteropException = nullptr;
    CallSetDirty_byPIQUdz9akDU2__zoHd1tg(target.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEditor


