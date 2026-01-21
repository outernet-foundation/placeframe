#include <DotNet/System/Collections/Generic/Enumerator0.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/String.h>
#include <DotNet/System/Collections/Generic/KeyValuePair2.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>



namespace DotNet::System::Collections::Generic {

Enumerator0::Enumerator0(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Enumerator0::Enumerator0(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Enumerator0::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Enumerator0::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Enumerator0::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Enumerator0::GetHandle() {
    return this->_handle;
}


void* (*DotNet::System::Collections::Generic::Enumerator0::Property_get_Current)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String> Enumerator0::Current() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Current((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::System::Collections::Generic::Enumerator0::CallMoveNext_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


bool Enumerator0::MoveNext() const {
    void* reinteropException = nullptr;
    auto result = CallMoveNext_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::System::Collections::Generic


