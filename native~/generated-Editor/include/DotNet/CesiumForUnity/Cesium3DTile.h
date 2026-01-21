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
namespace DotNet::Unity::Mathematics {
struct double4x4;
}

namespace DotNet::CesiumForUnity {

class Cesium3DTile {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Cesium3DTile(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Cesium3DTile(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: Cesium3DTile();
  public: operator ::DotNet::System::Object() const;
  private: static void (*Field_get__transform)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException);
  private: static void (*Field_set__transform)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* value, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double4x4 _transform() const;
  public: void _transform(const ::DotNet::Unity::Mathematics::double4x4& value) const;
  private: static void* (*Field_get__pTile)(void* thiz, void** reinteropException);
  private: static void (*Field_set__pTile)(void* thiz, void* value, void** reinteropException);
  public: void* _pTile() const;
  public: void _pTile(void* value) const;
  private: static void* (*Field_get__pTileEllipsoid)(void* thiz, void** reinteropException);
  private: static void (*Field_set__pTileEllipsoid)(void* thiz, void* value, void** reinteropException);
  public: void* _pTileEllipsoid() const;
  public: void _pTileEllipsoid(void* value) const;
};

} // namespace DotNet::CesiumForUnity


