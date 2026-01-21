#include <DotNet/UnityEditor/IMGUI/Controls/TreeViewState.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>



namespace DotNet::UnityEditor::IMGUI::Controls {

TreeViewState::TreeViewState(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TreeViewState::TreeViewState(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TreeViewState::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TreeViewState::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TreeViewState::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TreeViewState::GetHandle() {
    return this->_handle;
}


void* (*TreeViewState::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


TreeViewState::TreeViewState()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


TreeViewState::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


} // namespace DotNet::UnityEditor::IMGUI::Controls


