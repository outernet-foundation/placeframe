#include <DotNet/UnityEngine/GUI.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Rect.h>
#include <DotNet/System/String.h>

namespace DotNet::UnityEngine {
struct Rect;
}

namespace DotNet::UnityEngine {

GUI::GUI(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


GUI::GUI(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool GUI::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool GUI::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& GUI::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& GUI::GetHandle() {
    return this->_handle;
}


GUI::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::GUI::CallLabel_iRU7t71QqJzkr4BTYehN9A)(const ::DotNet::UnityEngine::Rect* position, void* text, void** reinteropException) = nullptr;


void GUI::Label(const ::DotNet::UnityEngine::Rect& position, const ::DotNet::System::String& text) {
    void* reinteropException = nullptr;
    CallLabel_iRU7t71QqJzkr4BTYehN9A(&position, text.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


