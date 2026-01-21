#include <DotNet/CesiumForUnity/CesiumFeature.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/System/Array1.h>
#include "CesiumFeatureImpl.h"
#include <cstdint>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/CesiumForUnity/MetadataType.h>



namespace DotNet::CesiumForUnity {

CesiumFeature::CesiumFeature(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumFeature::CesiumFeature(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumFeature::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumFeature::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumFeature::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumFeature::GetHandle() {
    return this->_handle;
}


void* (*CesiumFeature::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumFeature::CesiumFeature()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumFeature::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumFeature::Property_get_className)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumFeature::className() const {
    void* reinteropException = nullptr;
    auto result = Property_get_className((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumFeature::Property_set_className)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumFeature::className(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_className((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumFeature::Property_get_featureTableName)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumFeature::featureTableName() const {
    void* reinteropException = nullptr;
    auto result = Property_get_featureTableName((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumFeature::Property_set_featureTableName)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumFeature::featureTableName(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_featureTableName((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumFeature::Property_get_properties)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::System::String> CesiumFeature::properties() const {
    void* reinteropException = nullptr;
    auto result = Property_get_properties((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumFeature::Property_set_properties)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumFeature::properties(const ::DotNet::System::Array1<::DotNet::System::String>& value) const {
    void* reinteropException = nullptr;
    Property_set_properties((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*CesiumFeature::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumFeatureImpl& CesiumFeature::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumFeatureImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumFeature_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumFeatureImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumFeature_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int8_t DotNet_CesiumForUnity_CesiumFeature_GetInt8(void* handle, void* pImpl, void* property, ::std::int8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt8(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumFeature_GetUInt8(void* handle, void* pImpl, void* property, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt8(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::int16_t DotNet_CesiumForUnity_CesiumFeature_GetInt16(void* handle, void* pImpl, void* property, ::std::int16_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt16(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::uint16_t DotNet_CesiumForUnity_CesiumFeature_GetUInt16(void* handle, void* pImpl, void* property, ::std::uint16_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt16(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::int32_t DotNet_CesiumForUnity_CesiumFeature_GetInt32(void* handle, void* pImpl, void* property, ::std::int32_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt32(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::uint32_t DotNet_CesiumForUnity_CesiumFeature_GetUInt32(void* handle, void* pImpl, void* property, ::std::uint32_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt32(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::int64_t DotNet_CesiumForUnity_CesiumFeature_GetInt64(void* handle, void* pImpl, void* property, ::std::int64_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetInt64(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::uint64_t DotNet_CesiumForUnity_CesiumFeature_GetUInt64(void* handle, void* pImpl, void* property, ::std::uint64_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetUInt64(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
float DotNet_CesiumForUnity_CesiumFeature_GetFloat32(void* handle, void* pImpl, void* property, float defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat32(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
double DotNet_CesiumForUnity_CesiumFeature_GetFloat64(void* handle, void* pImpl, void* property, double defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetFloat64(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), defaultValue);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumFeature_GetBoolean(void* handle, void* pImpl, void* property, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetBoolean(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), !!defaultValue);
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
void* DotNet_CesiumForUnity_CesiumFeature_GetString(void* handle, void* pImpl, void* property, void* defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetString(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(defaultValue)));
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
::std::int8_t DotNet_CesiumForUnity_CesiumFeature_GetComponentInt8(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::int8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentInt8(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumFeature_GetComponentUInt8(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentUInt8(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::int16_t DotNet_CesiumForUnity_CesiumFeature_GetComponentInt16(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::int16_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentInt16(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::uint16_t DotNet_CesiumForUnity_CesiumFeature_GetComponentUInt16(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::uint16_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentUInt16(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::int32_t DotNet_CesiumForUnity_CesiumFeature_GetComponentInt32(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::int32_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentInt32(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::uint32_t DotNet_CesiumForUnity_CesiumFeature_GetComponentUInt32(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::uint32_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentUInt32(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::int64_t DotNet_CesiumForUnity_CesiumFeature_GetComponentInt64(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::int64_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentInt64(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::uint64_t DotNet_CesiumForUnity_CesiumFeature_GetComponentUInt64(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::uint64_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentUInt64(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
float DotNet_CesiumForUnity_CesiumFeature_GetComponentFloat32(void* handle, void* pImpl, void* property, ::std::int32_t index, float defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentFloat32(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
double DotNet_CesiumForUnity_CesiumFeature_GetComponentFloat64(void* handle, void* pImpl, void* property, ::std::int32_t index, double defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentFloat64(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, defaultValue);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumFeature_GetComponentBoolean(void* handle, void* pImpl, void* property, ::std::int32_t index, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentBoolean(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, !!defaultValue);
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
void* DotNet_CesiumForUnity_CesiumFeature_GetComponentString(void* handle, void* pImpl, void* property, ::std::int32_t index, void* defaultValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentString(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)), index, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(defaultValue)));
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
::std::int32_t DotNet_CesiumForUnity_CesiumFeature_GetComponentCount(void* handle, void* pImpl, void* property, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentCount(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)));
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
::std::uint32_t DotNet_CesiumForUnity_CesiumFeature_GetComponentType(void* handle, void* pImpl, void* property, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetComponentType(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)));
    return ::std::uint32_t(result);
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
::std::uint32_t DotNet_CesiumForUnity_CesiumFeature_GetMetadataType(void* handle, void* pImpl, void* property, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetMetadataType(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)));
    return ::std::uint32_t(result);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumFeature_IsNormalized(void* handle, void* pImpl, void* property, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumFeatureImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumFeature wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsNormalized(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(property)));
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

} // extern "C"

