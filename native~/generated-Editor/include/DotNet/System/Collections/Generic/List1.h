#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::CesiumForUnity {
class QuickAddItem;
}
namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::CesiumForUnity {
enum class GoogleMapTilesLayerType;
}
namespace DotNet::CesiumForUnity {
class HeaderEntry;
}
namespace DotNet::CesiumForUnity {
class CesiumCreditComponent;
}
namespace DotNet::CesiumForUnity {
class CesiumCredit;
}
namespace DotNet::UnityEngine {
class Texture2D;
}
namespace DotNet::Unity::Mathematics {
struct double2;
}
namespace DotNet::CesiumForUnity {
class CesiumCartographicPolygon;
}
namespace DotNet::UnityEngine {
class Camera;
}

namespace DotNet::System::Collections::Generic {

template <typename T0>
class List1;

template <> class List1<::DotNet::CesiumForUnity::QuickAddItem> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: List1();
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallAdd_nq8TJwFX_ptyb2rCV3CGsw)(void* thiz, void* item, void** reinteropException);
  public: void Add(const ::DotNet::CesiumForUnity::QuickAddItem& item) const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::System::String> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: List1();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::System::String operator[](::std::int32_t index) const;
  private: static void (*CallClear_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Clear() const;
  private: static void (*CallAdd_LRSjiXmrvb5pgfbcZ_Nv7w)(void* thiz, void* item, void** reinteropException);
  public: void Add(const ::DotNet::System::String& item) const;
  private: static void* (*CallToArray_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::System::String> ToArray() const;
};

template <typename T0>
class List1;

template <> class List1<::std::int32_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: List1();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static ::std::int32_t (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::std::int32_t operator[](::std::int32_t index) const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: List1();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static ::std::uint32_t (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::GoogleMapTilesLayerType operator[](::std::int32_t index) const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::CesiumForUnity::HeaderEntry> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::HeaderEntry operator[](::std::int32_t index) const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::CesiumForUnity::CesiumCreditComponent> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: List1();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static void (*CallAdd_VqNpQ4Sqmxp7DzXSAQsehQ)(void* thiz, void* item, void** reinteropException);
  public: void Add(const ::DotNet::CesiumForUnity::CesiumCreditComponent& item) const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::CesiumForUnity::CesiumCredit> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallAdd_DnUt__NGf__FxtU__keZH5Geg)(void* thiz, void* item, void** reinteropException);
  public: void Add(const ::DotNet::CesiumForUnity::CesiumCredit& item) const;
  private: static void (*CallClear_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Clear() const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::UnityEngine::Texture2D> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::Unity::Mathematics::double2> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static void (*Property_get_Item)(void* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double2 operator[](::std::int32_t index) const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::CesiumForUnity::CesiumCartographicPolygon> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumCartographicPolygon operator[](::std::int32_t index) const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
};

template <typename T0>
class List1;

template <> class List1<::DotNet::UnityEngine::Camera> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit List1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: List1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Count)(void* thiz, void** reinteropException);
  public: ::std::int32_t Count() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::UnityEngine::Camera operator[](::std::int32_t index) const;
};

} // namespace DotNet::System::Collections::Generic


