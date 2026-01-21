#include <DotNet/System/Array.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::System {

Array::Array(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Array::Array(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Array::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Array::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Array::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Array::GetHandle() {
    return this->_handle;
}


Array::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::System::Array::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Array::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::System


