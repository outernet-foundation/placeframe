#include <DotNet/CesiumForUnity/CesiumPropertyTableProperty.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumPropertyTablePropertyStatus.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValue.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValueType.h>
#include "CesiumPropertyTablePropertyImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>
#include <utility>
#include <DotNet/Unity/Mathematics/int2.h>
#include <DotNet/Unity/Mathematics/uint2.h>
#include <DotNet/Unity/Mathematics/float2.h>
#include <DotNet/Unity/Mathematics/double2.h>
#include <DotNet/Unity/Mathematics/int3.h>
#include <DotNet/Unity/Mathematics/uint3.h>
#include <DotNet/Unity/Mathematics/float3.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/Unity/Mathematics/int4.h>
#include <DotNet/Unity/Mathematics/uint4.h>
#include <DotNet/Unity/Mathematics/float4.h>
#include <DotNet/Unity/Mathematics/double4.h>
#include <DotNet/Unity/Mathematics/int2x2.h>
#include <DotNet/Unity/Mathematics/uint2x2.h>
#include <DotNet/Unity/Mathematics/float2x2.h>
#include <DotNet/Unity/Mathematics/double2x2.h>
#include <DotNet/Unity/Mathematics/int3x3.h>
#include <DotNet/Unity/Mathematics/uint3x3.h>
#include <DotNet/Unity/Mathematics/float3x3.h>
#include <DotNet/Unity/Mathematics/double3x3.h>
#include <DotNet/Unity/Mathematics/int4x4.h>
#include <DotNet/Unity/Mathematics/uint4x4.h>
#include <DotNet/Unity/Mathematics/float4x4.h>
#include <DotNet/Unity/Mathematics/double4x4.h>
#include <DotNet/CesiumForUnity/CesiumPropertyArray.h>

namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}

namespace DotNet::CesiumForUnity {

CesiumPropertyTableProperty::CesiumPropertyTableProperty(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumPropertyTableProperty::CesiumPropertyTableProperty(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumPropertyTableProperty::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumPropertyTableProperty::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumPropertyTableProperty::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumPropertyTableProperty::GetHandle() {
    return this->_handle;
}


void* (*CesiumPropertyTableProperty::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumPropertyTableProperty::CesiumPropertyTableProperty()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumPropertyTableProperty::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_status)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumPropertyTablePropertyStatus CesiumPropertyTableProperty::status() const {
    void* reinteropException = nullptr;
    auto result = Property_get_status((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPropertyTablePropertyStatus(result);
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_status)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::status(::DotNet::CesiumForUnity::CesiumPropertyTablePropertyStatus value) const {
    void* reinteropException = nullptr;
    Property_set_status((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_size)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumPropertyTableProperty::size() const {
    void* reinteropException = nullptr;
    auto result = Property_get_size((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_size)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::size(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_size((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_arraySize)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumPropertyTableProperty::arraySize() const {
    void* reinteropException = nullptr;
    auto result = Property_get_arraySize((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_arraySize)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::arraySize(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_arraySize((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_isNormalized)(void* thiz, void** reinteropException) = nullptr;


bool CesiumPropertyTableProperty::isNormalized() const {
    void* reinteropException = nullptr;
    auto result = Property_get_isNormalized((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_isNormalized)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::isNormalized(bool value) const {
    void* reinteropException = nullptr;
    Property_set_isNormalized((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_offset)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue CesiumPropertyTableProperty::offset() const {
    void* reinteropException = nullptr;
    auto result = Property_get_offset((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_offset)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::offset(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const {
    void* reinteropException = nullptr;
    Property_set_offset((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_scale)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue CesiumPropertyTableProperty::scale() const {
    void* reinteropException = nullptr;
    auto result = Property_get_scale((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_scale)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::scale(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const {
    void* reinteropException = nullptr;
    Property_set_scale((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_min)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue CesiumPropertyTableProperty::min() const {
    void* reinteropException = nullptr;
    auto result = Property_get_min((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_min)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::min(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const {
    void* reinteropException = nullptr;
    Property_set_min((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_max)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue CesiumPropertyTableProperty::max() const {
    void* reinteropException = nullptr;
    auto result = Property_get_max((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_max)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::max(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const {
    void* reinteropException = nullptr;
    Property_set_max((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_noData)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue CesiumPropertyTableProperty::noData() const {
    void* reinteropException = nullptr;
    auto result = Property_get_noData((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_noData)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::noData(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const {
    void* reinteropException = nullptr;
    Property_set_noData((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_defaultValue)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValue CesiumPropertyTableProperty::defaultValue() const {
    void* reinteropException = nullptr;
    auto result = Property_get_defaultValue((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_defaultValue)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::defaultValue(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const {
    void* reinteropException = nullptr;
    Property_set_defaultValue((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_get_valueType)(void* thiz, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValueType CesiumPropertyTableProperty::valueType() const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumMetadataValueType result;
    Property_get_valueType((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumPropertyTableProperty::Property_set_valueType)(void* thiz, const ::DotNet::CesiumForUnity::CesiumMetadataValueType* value, void** reinteropException) = nullptr;


void CesiumPropertyTableProperty::valueType(const ::DotNet::CesiumForUnity::CesiumMetadataValueType& value) const {
    void* reinteropException = nullptr;
    Property_set_valueType((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*CesiumPropertyTableProperty::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumPropertyTablePropertyImpl& CesiumPropertyTableProperty::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumPropertyTableProperty_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumPropertyTablePropertyImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetBoolean(void* handle, void* pImpl, ::std::int64_t featureID, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetBoolean(wrapper, featureID, !!defaultValue);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int8_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetSByte(void* handle, void* pImpl, ::std::int64_t featureID, ::std::int8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetSByte(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetByte(void* handle, void* pImpl, ::std::int64_t featureID, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetByte(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int16_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt16(void* handle, void* pImpl, ::std::int64_t featureID, ::std::int16_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt16(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int16_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int16_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int16_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint16_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt16(void* handle, void* pImpl, ::std::int64_t featureID, ::std::uint16_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt16(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint16_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint16_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint16_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int32_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt32(void* handle, void* pImpl, ::std::int64_t featureID, ::std::int32_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt32(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int32_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int32_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int32_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint32_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt32(void* handle, void* pImpl, ::std::int64_t featureID, ::std::uint32_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt32(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint32_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint32_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint32_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int64_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt64(void* handle, void* pImpl, ::std::int64_t featureID, ::std::int64_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt64(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint64_t DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt64(void* handle, void* pImpl, ::std::int64_t featureID, ::std::uint64_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt64(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
float DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat(void* handle, void* pImpl, ::std::int64_t featureID, float defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return float();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return float();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return float();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
double DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble(void* handle, void* pImpl, ::std::int64_t featureID, double defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble(wrapper, featureID, defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return double();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return double();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return double();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::int2* defaultValue, ::DotNet::Unity::Mathematics::int2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::uint2* defaultValue, ::DotNet::Unity::Mathematics::uint2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::float2* defaultValue, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::double2* defaultValue, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::int3* defaultValue, ::DotNet::Unity::Mathematics::int3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::uint3* defaultValue, ::DotNet::Unity::Mathematics::uint3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::float3* defaultValue, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::double3* defaultValue, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::int4* defaultValue, ::DotNet::Unity::Mathematics::int4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::uint4* defaultValue, ::DotNet::Unity::Mathematics::uint4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::float4* defaultValue, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::double4* defaultValue, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt2x2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::int2x2* defaultValue, ::DotNet::Unity::Mathematics::int2x2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt2x2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt2x2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::uint2x2* defaultValue, ::DotNet::Unity::Mathematics::uint2x2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt2x2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat2x2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::float2x2* defaultValue, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat2x2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble2x2(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::double2x2* defaultValue, ::DotNet::Unity::Mathematics::double2x2* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble2x2(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt3x3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::int3x3* defaultValue, ::DotNet::Unity::Mathematics::int3x3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt3x3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt3x3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::uint3x3* defaultValue, ::DotNet::Unity::Mathematics::uint3x3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt3x3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat3x3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::float3x3* defaultValue, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat3x3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble3x3(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::double3x3* defaultValue, ::DotNet::Unity::Mathematics::double3x3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble3x3(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetInt4x4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::int4x4* defaultValue, ::DotNet::Unity::Mathematics::int4x4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt4x4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetUInt4x4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::uint4x4* defaultValue, ::DotNet::Unity::Mathematics::uint4x4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt4x4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetFloat4x4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::float4x4* defaultValue, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat4x4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetDouble4x4(void* handle, void* pImpl, ::std::int64_t featureID, const ::DotNet::Unity::Mathematics::double4x4* defaultValue, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetDouble4x4(wrapper, featureID, *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetString(void* handle, void* pImpl, ::std::int64_t featureID, void* defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetString(wrapper, featureID, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(defaultValue)));
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetArray(void* handle, void* pImpl, ::std::int64_t featureID, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetArray(wrapper, featureID);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetValue(void* handle, void* pImpl, ::std::int64_t featureID, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetValue(wrapper, featureID);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumPropertyTableProperty_GetRawValue(void* handle, void* pImpl, ::std::int64_t featureID, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumPropertyTablePropertyImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetRawValue(wrapper, featureID);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}

} // extern "C"

