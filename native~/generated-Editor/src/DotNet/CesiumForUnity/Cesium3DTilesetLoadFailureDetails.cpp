#include <DotNet/CesiumForUnity/Cesium3DTilesetLoadFailureDetails.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/CesiumForUnity/Cesium3DTilesetLoadType.h>
#include <DotNet/System/String.h>



namespace DotNet::CesiumForUnity {

Cesium3DTilesetLoadFailureDetails::Cesium3DTilesetLoadFailureDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Cesium3DTilesetLoadFailureDetails::Cesium3DTilesetLoadFailureDetails(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Cesium3DTilesetLoadFailureDetails::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Cesium3DTilesetLoadFailureDetails::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Cesium3DTilesetLoadFailureDetails::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Cesium3DTilesetLoadFailureDetails::GetHandle() {
    return this->_handle;
}


void* (*Cesium3DTilesetLoadFailureDetails::Construct_lQ2_FlEU3TadAE4hjbl4Mw)(void* tileset, ::std::uint32_t type, ::std::int64_t httpStatusCode, void* message, void** reinteropException) = nullptr;


Cesium3DTilesetLoadFailureDetails::Cesium3DTilesetLoadFailureDetails(const ::DotNet::CesiumForUnity::Cesium3DTileset& tileset, ::DotNet::CesiumForUnity::Cesium3DTilesetLoadType type, ::std::int64_t httpStatusCode, const ::DotNet::System::String& message)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_lQ2_FlEU3TadAE4hjbl4Mw(tileset.GetHandle().GetRaw(), ::std::uint32_t(type), httpStatusCode, message.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


} // namespace DotNet::CesiumForUnity


