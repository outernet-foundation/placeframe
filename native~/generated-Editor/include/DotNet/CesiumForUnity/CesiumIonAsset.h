#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class Cesium3DTileset;
}
namespace DotNet::CesiumForUnity {
class CesiumIonRasterOverlay;
}

namespace DotNet::CesiumForUnity {

class CesiumIonAsset {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumIonAsset(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumIonAsset(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_objectName)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String objectName() const;
  private: static void* (*Property_get_type)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String type() const;
  private: static void* (*Property_get_componentType)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String componentType() const;
  private: static void* (*Property_get_ionAccessToken)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String ionAccessToken() const;
  private: static void (*Property_set_ionAccessToken)(void* thiz, void* value, void** reinteropException);
  public: void ionAccessToken(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Property_get_ionAssetID)(void* thiz, void** reinteropException);
  public: ::std::int64_t ionAssetID() const;
  private: static void* (*Property_get_tileset)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::Cesium3DTileset tileset() const;
  private: static void* (*Property_get_overlay)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonRasterOverlay overlay() const;
  private: static ::std::uint8_t (*CallIsNull_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: bool IsNull() const;
};

} // namespace DotNet::CesiumForUnity


