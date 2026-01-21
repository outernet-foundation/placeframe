#include <DotNet/CesiumForUnity/IonAssetDetails.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::CesiumForUnity {

IonAssetDetails::IonAssetDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


IonAssetDetails::IonAssetDetails(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool IonAssetDetails::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool IonAssetDetails::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& IonAssetDetails::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& IonAssetDetails::GetHandle() {
    return this->_handle;
}


IonAssetDetails::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::IonAssetDetails::CallFormatType_3GczHehc_XCRt9ReXGSrdQ)(void* type, void** reinteropException) = nullptr;


::DotNet::System::String IonAssetDetails::FormatType(const ::DotNet::System::String& type) {
    void* reinteropException = nullptr;
    auto result = CallFormatType_3GczHehc_XCRt9ReXGSrdQ(type.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::IonAssetDetails::CallFormatDate_Wg__UxSmEJUgHx3kyfccFEw)(void* assetDate, void** reinteropException) = nullptr;


::DotNet::System::String IonAssetDetails::FormatDate(const ::DotNet::System::String& assetDate) {
    void* reinteropException = nullptr;
    auto result = CallFormatDate_Wg__UxSmEJUgHx3kyfccFEw(assetDate.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity


