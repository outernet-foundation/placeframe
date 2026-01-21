#include <DotNet/UnityEngine/Coroutine.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>



namespace DotNet::UnityEngine {

Coroutine::Coroutine(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Coroutine::Coroutine(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Coroutine::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Coroutine::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Coroutine::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Coroutine::GetHandle() {
    return this->_handle;
}


Coroutine::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


} // namespace DotNet::UnityEngine


