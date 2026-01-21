#include <DotNet/CesiumForUnity/TestGltfModel.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include "TestGltfModelImpl.h"
#include <DotNet/CesiumForUnity/CesiumFeatureIdAttribute.h>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/System/Array1.h>
#include <DotNet/CesiumForUnity/CesiumFeatureIdTexture.h>
#include <DotNet/Unity/Mathematics/float2.h>
#include <DotNet/CesiumForUnity/CesiumPropertyTableProperty.h>
#include <DotNet/Unity/Mathematics/float3.h>
#include <DotNet/Unity/Mathematics/float4.h>
#include <DotNet/Unity/Mathematics/float2x2.h>
#include <DotNet/Unity/Mathematics/float3x3.h>
#include <DotNet/Unity/Mathematics/float4x4.h>



namespace DotNet::CesiumForUnity {

TestGltfModel::TestGltfModel(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TestGltfModel::TestGltfModel(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TestGltfModel::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TestGltfModel::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TestGltfModel::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TestGltfModel::GetHandle() {
    return this->_handle;
}


void* (*TestGltfModel::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


TestGltfModel::TestGltfModel()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


TestGltfModel::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*TestGltfModel::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::TestGltfModelImpl& TestGltfModel::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::TestGltfModelImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_TestGltfModel_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::TestGltfModelImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_TestGltfModel_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_TestGltfModel_AddFeatureIdAttribute(void* handle, void* pImpl, void* featureIds, ::std::int64_t featureCount, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddFeatureIdAttribute(wrapper, ::DotNet::System::Array1<::std::uint16_t>(::DotNet::Reinterop::ObjectHandle(featureIds)), featureCount);
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
void* DotNet_CesiumForUnity_TestGltfModel_AddFeatureIdTexture(void* handle, void* pImpl, void* featureIds, ::std::int64_t featureCount, void* uvs, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddFeatureIdTexture(wrapper, ::DotNet::System::Array1<::std::uint16_t>(::DotNet::Reinterop::ObjectHandle(featureIds)), featureCount, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>(::DotNet::Reinterop::ObjectHandle(uvs)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddBooleanPropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddBooleanPropertyTableProperty(wrapper, ::DotNet::System::Array1<bool>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddIntPropertyTableProperty(void* handle, void* pImpl, void* values, ::std::uint8_t normalized, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddIntPropertyTableProperty(wrapper, ::DotNet::System::Array1<::std::int32_t>(::DotNet::Reinterop::ObjectHandle(values)), !!normalized);
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
void* DotNet_CesiumForUnity_TestGltfModel_AddDoublePropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddDoublePropertyTableProperty(wrapper, ::DotNet::System::Array1<double>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddVec2PropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddVec2PropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddVec3PropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddVec3PropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddVec4PropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddVec4PropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddMat2PropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddMat2PropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float2x2>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddMat3PropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddMat3PropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float3x3>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddMat4PropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddMat4PropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::float4x4>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddStringPropertyTableProperty(void* handle, void* pImpl, void* values, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddStringPropertyTableProperty(wrapper, ::DotNet::System::Array1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(values)));
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
void* DotNet_CesiumForUnity_TestGltfModel_AddFixedLengthArrayPropertyTableProperty(void* handle, void* pImpl, void* values, ::std::int64_t count, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddFixedLengthArrayPropertyTableProperty(wrapper, ::DotNet::System::Array1<double>(::DotNet::Reinterop::ObjectHandle(values)), count);
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
void* DotNet_CesiumForUnity_TestGltfModel_AddVariableLengthArrayPropertyTableProperty(void* handle, void* pImpl, void* values, void* offsets, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::TestGltfModelImpl*>(pImpl);const ::DotNet::CesiumForUnity::TestGltfModel wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->AddVariableLengthArrayPropertyTableProperty(wrapper, ::DotNet::System::Array1<double>(::DotNet::Reinterop::ObjectHandle(values)), ::DotNet::System::Array1<::std::uint16_t>(::DotNet::Reinterop::ObjectHandle(offsets)));
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

