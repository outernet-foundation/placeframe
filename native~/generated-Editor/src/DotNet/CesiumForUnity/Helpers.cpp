#include <DotNet/CesiumForUnity/Helpers.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/RuntimePlatform.h>



namespace DotNet::CesiumForUnity {

Helpers::Helpers(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Helpers::Helpers(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Helpers::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Helpers::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Helpers::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Helpers::GetHandle() {
    return this->_handle;
}


Helpers::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::Helpers::CallToString__8pn__Nas4aiRxhf1NkpeKg)(::std::uint32_t value, void** reinteropException) = nullptr;


template <> ::DotNet::System::String Helpers::ToString<::DotNet::UnityEngine::RuntimePlatform>(const ::DotNet::UnityEngine::RuntimePlatform& value) {
    void* reinteropException = nullptr;
    auto result = CallToString__8pn__Nas4aiRxhf1NkpeKg(::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity


