#include <DotNet/CesiumForUnity/CesiumRasterOverlayLoadFailureDetails.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumRasterOverlay.h>
#include <DotNet/CesiumForUnity/CesiumRasterOverlayLoadType.h>
#include <DotNet/System/String.h>



namespace DotNet::CesiumForUnity {

CesiumRasterOverlayLoadFailureDetails::CesiumRasterOverlayLoadFailureDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumRasterOverlayLoadFailureDetails::CesiumRasterOverlayLoadFailureDetails(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumRasterOverlayLoadFailureDetails::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumRasterOverlayLoadFailureDetails::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumRasterOverlayLoadFailureDetails::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumRasterOverlayLoadFailureDetails::GetHandle() {
    return this->_handle;
}


void* (*CesiumRasterOverlayLoadFailureDetails::Construct___R__AqUOiZnUHIgxRnspXXw)(void* overlay, ::std::uint32_t type, ::std::int64_t httpStatusCode, void* message, void** reinteropException) = nullptr;


CesiumRasterOverlayLoadFailureDetails::CesiumRasterOverlayLoadFailureDetails(const ::DotNet::CesiumForUnity::CesiumRasterOverlay& overlay, ::DotNet::CesiumForUnity::CesiumRasterOverlayLoadType type, ::std::int64_t httpStatusCode, const ::DotNet::System::String& message)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct___R__AqUOiZnUHIgxRnspXXw(overlay.GetHandle().GetRaw(), ::std::uint32_t(type), httpStatusCode, message.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


} // namespace DotNet::CesiumForUnity


