#include <DotNet/CesiumForUnity/CesiumWgs84Ellipsoid.h>
#include <utility>
#include "CesiumWgs84EllipsoidImpl.h"
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>
#include <optional>



namespace DotNet::CesiumForUnity {



} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumWgs84Ellipsoid_GetRadii(::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumWgs84EllipsoidImpl::GetRadii();
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
::std::uint8_t DotNet_CesiumForUnity_CesiumWgs84Ellipsoid_ScaleToGeodeticSurface(const ::DotNet::Unity::Mathematics::double3* earthCenteredEarthFixed, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumWgs84EllipsoidImpl::ScaleToGeodeticSurface(*earthCenteredEarthFixed);
    if (result.has_value()) { *pReturnValue = std::move(result.value()); return true; } else { return false; }
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
void DotNet_CesiumForUnity_CesiumWgs84Ellipsoid_GeodeticSurfaceNormal(const ::DotNet::Unity::Mathematics::double3* earthCenteredEarthFixed, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumWgs84EllipsoidImpl::GeodeticSurfaceNormal(*earthCenteredEarthFixed);
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
void DotNet_CesiumForUnity_CesiumWgs84Ellipsoid_LongitudeLatitudeHeightToEarthCenteredEarthFixed(const ::DotNet::Unity::Mathematics::double3* longitudeLatitudeHeight, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumWgs84EllipsoidImpl::LongitudeLatitudeHeightToEarthCenteredEarthFixed(*longitudeLatitudeHeight);
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
void DotNet_CesiumForUnity_CesiumWgs84Ellipsoid_EarthCenteredEarthFixedToLongitudeLatitudeHeight(const ::DotNet::Unity::Mathematics::double3* earthCenteredEarthFixed, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumWgs84EllipsoidImpl::EarthCenteredEarthFixedToLongitudeLatitudeHeight(*earthCenteredEarthFixed);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

