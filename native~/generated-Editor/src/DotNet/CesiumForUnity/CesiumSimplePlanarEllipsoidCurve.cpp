#include <DotNet/CesiumForUnity/CesiumSimplePlanarEllipsoidCurve.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumEllipsoid.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include "CesiumSimplePlanarEllipsoidCurveImpl.h"
#include <utility>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>

namespace DotNet::Unity::Mathematics {
struct double3;
}

namespace DotNet::CesiumForUnity {

CesiumSimplePlanarEllipsoidCurve::CesiumSimplePlanarEllipsoidCurve(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumSimplePlanarEllipsoidCurve::CesiumSimplePlanarEllipsoidCurve(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumSimplePlanarEllipsoidCurve::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumSimplePlanarEllipsoidCurve::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumSimplePlanarEllipsoidCurve::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumSimplePlanarEllipsoidCurve::GetHandle() {
    return this->_handle;
}


CesiumSimplePlanarEllipsoidCurve::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve::CallFromCenteredFixedCoordinates_Xlu0WX31sapbYyKKJDYoaw)(void* ellipsoid, const ::DotNet::Unity::Mathematics::double3* sourceEcef, const ::DotNet::Unity::Mathematics::double3* destinationEcef, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve CesiumSimplePlanarEllipsoidCurve::FromCenteredFixedCoordinates(const ::DotNet::CesiumForUnity::CesiumEllipsoid& ellipsoid, const ::DotNet::Unity::Mathematics::double3& sourceEcef, const ::DotNet::Unity::Mathematics::double3& destinationEcef) {
    void* reinteropException = nullptr;
    auto result = CallFromCenteredFixedCoordinates_Xlu0WX31sapbYyKKJDYoaw(ellipsoid.GetHandle().GetRaw(), &sourceEcef, &destinationEcef, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*CesiumSimplePlanarEllipsoidCurve::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl& CesiumSimplePlanarEllipsoidCurve::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumSimplePlanarEllipsoidCurve_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumSimplePlanarEllipsoidCurve_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumSimplePlanarEllipsoidCurve_GetPosition(void* handle, void* pImpl, double percentage, double additionalHeight, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetPosition(wrapper, percentage, additionalHeight);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumSimplePlanarEllipsoidCurve_CreateFromCenteredFixed(void* handle, void* pImpl, void* ellipsoid, const ::DotNet::Unity::Mathematics::double3* sourceEcef, const ::DotNet::Unity::Mathematics::double3* destinationEcef, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->CreateFromCenteredFixed(wrapper, ::DotNet::CesiumForUnity::CesiumEllipsoid(::DotNet::Reinterop::ObjectHandle(ellipsoid)), *sourceEcef, *destinationEcef);
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
::std::uint8_t DotNet_CesiumForUnity_CesiumSimplePlanarEllipsoidCurve_CreateFromLongitudeLatitudeHeight(void* handle, void* pImpl, void* ellipsoid, const ::DotNet::Unity::Mathematics::double3* sourceLlh, const ::DotNet::Unity::Mathematics::double3* destinationLlh, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->CreateFromLongitudeLatitudeHeight(wrapper, ::DotNet::CesiumForUnity::CesiumEllipsoid(::DotNet::Reinterop::ObjectHandle(ellipsoid)), *sourceLlh, *destinationLlh);
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

