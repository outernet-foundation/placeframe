#include <DotNet/CesiumForUnity/Cesium3DTile.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/Unity/Mathematics/double4x4.h>
#include <utility>
#include "Cesium3DTileImpl.h"
#include <DotNet/UnityEngine/Bounds.h>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>

namespace DotNet::Unity::Mathematics {
struct double4x4;
}

namespace DotNet::CesiumForUnity {

Cesium3DTile::Cesium3DTile(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Cesium3DTile::Cesium3DTile(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Cesium3DTile::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Cesium3DTile::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Cesium3DTile::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Cesium3DTile::GetHandle() {
    return this->_handle;
}


void* (*Cesium3DTile::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


Cesium3DTile::Cesium3DTile()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


Cesium3DTile::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::CesiumForUnity::Cesium3DTile::Field_get__transform)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::Cesium3DTile::Field_set__transform)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double4x4 Cesium3DTile::_transform() const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4x4 result;
    Field_get__transform((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void Cesium3DTile::_transform(const ::DotNet::Unity::Mathematics::double4x4& value) const {
    void* reinteropException = nullptr;
    Field_set__transform((*this).GetHandle().GetRaw(), &value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::Cesium3DTile::Field_get__pTile)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::Cesium3DTile::Field_set__pTile)(void* thiz, void* value, void** reinteropException) = nullptr;


void* Cesium3DTile::_pTile() const {
    void* reinteropException = nullptr;
    auto result = Field_get__pTile((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void Cesium3DTile::_pTile(void* value) const {
    void* reinteropException = nullptr;
    Field_set__pTile((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::Cesium3DTile::Field_get__pTileEllipsoid)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::Cesium3DTile::Field_set__pTileEllipsoid)(void* thiz, void* value, void** reinteropException) = nullptr;


void* Cesium3DTile::_pTileEllipsoid() const {
    void* reinteropException = nullptr;
    auto result = Field_get__pTileEllipsoid((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void Cesium3DTile::_pTileEllipsoid(void* value) const {
    void* reinteropException = nullptr;
    Field_set__pTileEllipsoid((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_Cesium3DTile_getBounds(void* pTile, void* pTileEllipsoid, const ::DotNet::Unity::Mathematics::double4x4* ecefToLocalMatrix, ::DotNet::UnityEngine::Bounds* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::Cesium3DTileImpl::getBounds(pTile, pTileEllipsoid, *ecefToLocalMatrix);
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

