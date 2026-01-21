#include <DotNet/CesiumForUnity/CesiumCreditComponent.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/System/Object.h>



namespace DotNet::CesiumForUnity {

CesiumCreditComponent::CesiumCreditComponent(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumCreditComponent::CesiumCreditComponent(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumCreditComponent::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumCreditComponent::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumCreditComponent::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumCreditComponent::GetHandle() {
    return this->_handle;
}


void* (*CesiumCreditComponent::Construct_hnJK39H7_p9CsaJF5ySJ5Q)(void* text, void* link, ::std::int32_t imageId, void** reinteropException) = nullptr;


CesiumCreditComponent::CesiumCreditComponent(const ::DotNet::System::String& text, const ::DotNet::System::String& link, ::std::int32_t imageId)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_hnJK39H7_p9CsaJF5ySJ5Q(text.GetHandle().GetRaw(), link.GetHandle().GetRaw(), imageId, &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumCreditComponent::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


} // namespace DotNet::CesiumForUnity


