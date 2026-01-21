#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Array;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
class Cesium3DTileset;
}
namespace DotNet::CesiumForUnity {
class CesiumRasterOverlay;
}
namespace DotNet::CesiumForUnity {
class CesiumIonRasterOverlay;
}
namespace DotNet::UnityEngine {
class Mesh;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumFeature;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine::Rendering {
struct VertexAttributeDescriptor;
}
namespace DotNet::CesiumForUnity {
class CesiumGlobeAnchor;
}
namespace DotNet::CesiumForUnity {
class CesiumTileExcluder;
}
namespace DotNet::CesiumForUnity {
class CesiumMetadataValue;
}
namespace DotNet::CesiumForUnity {
class CesiumFeatureIdSet;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyTable;
}
namespace DotNet::Unity::Mathematics {
struct float2;
}
namespace DotNet::Unity::Mathematics {
struct float3;
}
namespace DotNet::Unity::Mathematics {
struct float4;
}
namespace DotNet::Unity::Mathematics {
struct float2x2;
}
namespace DotNet::Unity::Mathematics {
struct float3x3;
}
namespace DotNet::Unity::Mathematics {
struct float4x4;
}
namespace DotNet::Unity::Mathematics {
struct double3;
}

namespace DotNet::System {

template <typename T0>
class Array1;

template <> class Array1<::std::uint8_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, ::std::uint8_t value);
  public: void Item(std::int32_t index, ::std::uint8_t value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::Cesium3DTileset> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::Cesium3DTileset operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::Cesium3DTileset& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumRasterOverlay> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumRasterOverlay operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumRasterOverlay& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumIonRasterOverlay> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonRasterOverlay operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumIonRasterOverlay& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::UnityEngine::Mesh> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::UnityEngine::Mesh operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::UnityEngine::Mesh& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::UnityEngine::Vector3> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Vector3 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::UnityEngine::Vector3* value);
  public: void Item(std::int32_t index, const ::DotNet::UnityEngine::Vector3& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::System::String> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::System::String operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::System::String& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumFeature> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumFeature operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumFeature& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::UnityEngine::GameObject> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::UnityEngine::GameObject operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::UnityEngine::GameObject& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor* pReturnValue, void** reinteropException);
  public: ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor* value);
  public: void Item(std::int32_t index, const ::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumGlobeAnchor> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumGlobeAnchor operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumGlobeAnchor& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumTileExcluder> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumTileExcluder operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumTileExcluder& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumMetadataValue> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumMetadataValue& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumFeatureIdSet> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumFeatureIdSet operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumFeatureIdSet& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::CesiumForUnity::CesiumPropertyTable> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumPropertyTable operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, void* value);
  public: void Item(std::int32_t index, const ::DotNet::CesiumForUnity::CesiumPropertyTable& value);
};

template <typename T0>
class Array1;

template <> class Array1<bool> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: bool operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, ::std::uint8_t value);
  public: void Item(std::int32_t index, bool value);
};

template <typename T0>
class Array1;

template <> class Array1<::std::uint16_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint16_t (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::uint16_t operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, ::std::uint16_t value);
  public: void Item(std::int32_t index, ::std::uint16_t value);
};

template <typename T0>
class Array1;

template <> class Array1<::std::int32_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::int32_t operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, ::std::int32_t value);
  public: void Item(std::int32_t index, ::std::int32_t value);
};

template <typename T0>
class Array1;

template <> class Array1<double> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static double (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: double operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, double value);
  public: void Item(std::int32_t index, double value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::float2> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float2 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::float2* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float2& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::float3> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float3 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::float3* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float3& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::float4> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float4 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::float4* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float4& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::float2x2> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float2x2 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::float2x2* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float2x2& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::float3x3> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float3x3 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::float3x3* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float3x3& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::float4x4> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::float4x4 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::float4x4* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::float4x4& value);
};

template <typename T0>
class Array1;

template <> class Array1<::DotNet::Unity::Mathematics::double3> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Array1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Array1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Array() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double3 operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Construct_Size)(std::int32_t size);
  public: Array1(std::int32_t size);
  private: static void (*SetItem)(void* thiz, std::int32_t index, const ::DotNet::Unity::Mathematics::double3* value);
  public: void Item(std::int32_t index, const ::DotNet::Unity::Mathematics::double3& value);
};

} // namespace DotNet::System


