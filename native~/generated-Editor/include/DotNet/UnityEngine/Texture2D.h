#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
enum class TextureFormat;
}
namespace DotNet::UnityEngine {
class Texture;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}
namespace DotNet::UnityEngine {
enum class TextureWrapMode;
}
namespace DotNet::UnityEngine {
enum class FilterMode;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::UnityEngine {

class Texture2D {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Texture2D(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Texture2D(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_7_RAqfRCmreonOQ53TO4Og)(::std::int32_t width, ::std::int32_t height, ::std::uint32_t textureFormat, ::std::uint8_t mipChain, ::std::uint8_t linear, void** reinteropException);
  public: Texture2D(::std::int32_t width, ::std::int32_t height, ::DotNet::UnityEngine::TextureFormat textureFormat, bool mipChain, bool linear);
  private: static void* (*Construct_IFL2bOqlLrYHuwg5z0d8Cg)(::std::int32_t width, ::std::int32_t height, ::std::uint32_t textureFormat, ::std::int32_t mipCount, ::std::uint8_t linear, void** reinteropException);
  public: Texture2D(::std::int32_t width, ::std::int32_t height, ::DotNet::UnityEngine::TextureFormat textureFormat, ::std::int32_t mipCount, bool linear);
  public: operator ::DotNet::UnityEngine::Texture() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallLoadRawTextureData_C8JeOQhDs2O3mbZ4aC21YA)(void* thiz, void* data, ::std::int32_t size, void** reinteropException);
  public: void LoadRawTextureData(void* data, ::std::int32_t size) const;
  public: template <typename T>
  ::DotNet::Unity::Collections::NativeArray1<T> GetRawTextureData() const;
  private: static void* (*CallGetRawTextureData_z79ECk55IqLfMIqXBYg_8w)(void* thiz, void** reinteropException);
  private: static void (*CallApply_FZiaA8ur57jmvHTqox9Bng)(void* thiz, ::std::uint8_t updateMipmaps, ::std::uint8_t makeNoLongerReadable, void** reinteropException);
  public: void Apply(bool updateMipmaps, bool makeNoLongerReadable) const;
  private: static ::std::uint32_t (*Property_get_wrapMode)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::TextureWrapMode wrapMode() const;
  private: static void (*Property_set_wrapMode)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void wrapMode(::DotNet::UnityEngine::TextureWrapMode value) const;
  private: static ::std::int32_t (*Property_get_anisoLevel)(void* thiz, void** reinteropException);
  public: ::std::int32_t anisoLevel() const;
  private: static void (*Property_set_anisoLevel)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void anisoLevel(::std::int32_t value) const;
  private: static ::std::uint32_t (*Property_get_filterMode)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::FilterMode filterMode() const;
  private: static void (*Property_set_filterMode)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void filterMode(::DotNet::UnityEngine::FilterMode value) const;
  private: static ::std::uint32_t (*Property_get_wrapModeU)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::TextureWrapMode wrapModeU() const;
  private: static void (*Property_set_wrapModeU)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void wrapModeU(::DotNet::UnityEngine::TextureWrapMode value) const;
  private: static ::std::uint32_t (*Property_get_wrapModeV)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::TextureWrapMode wrapModeV() const;
  private: static void (*Property_set_wrapModeV)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void wrapModeV(::DotNet::UnityEngine::TextureWrapMode value) const;
  private: static ::std::uint32_t (*Property_get_wrapModeW)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::TextureWrapMode wrapModeW() const;
  private: static void (*Property_set_wrapModeW)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void wrapModeW(::DotNet::UnityEngine::TextureWrapMode value) const;
  private: static void* (*Property_get_name)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String name() const;
  private: static void (*Property_set_name)(void* thiz, void* value, void** reinteropException);
  public: void name(const ::DotNet::System::String& value) const;
  private: static ::std::uint32_t (*Property_get_hideFlags)(void* thiz, void** reinteropException);
  public: ::flags::flags<::DotNet::UnityEngine::HideFlags> hideFlags() const;
  private: static void (*Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const;
  private: static ::std::uint8_t (*Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator==(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator==(const Texture2D& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const Texture2D& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::UnityEngine


