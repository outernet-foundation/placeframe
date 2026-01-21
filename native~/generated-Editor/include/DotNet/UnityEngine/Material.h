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
class Object;
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
namespace DotNet::UnityEngine {
class Shader;
}
namespace DotNet::UnityEngine {
class Texture;
}
namespace DotNet::UnityEngine {
struct Vector4;
}
namespace DotNet::UnityEngine {
struct Vector2;
}
namespace DotNet::System::Collections::Generic {
template <typename T0> class List1;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::UnityEngine {

class Material {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Material(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Material(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_shaderKeywords)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::System::String> shaderKeywords() const;
  private: static void (*Property_set_shaderKeywords)(void* thiz, void* value, void** reinteropException);
  public: void shaderKeywords(const ::DotNet::System::Array1<::DotNet::System::String>& value) const;
  private: static void* (*Property_get_shader)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Shader shader() const;
  private: static void (*Property_set_shader)(void* thiz, void* value, void** reinteropException);
  public: void shader(const ::DotNet::UnityEngine::Shader& value) const;
  private: static ::std::int32_t (*CallComputeCRC_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t ComputeCRC() const;
  private: static void (*CallSetTexture_RautZzWeb93ejEP2lTHyaQ)(void* thiz, ::std::int32_t nameID, void* value, void** reinteropException);
  public: void SetTexture(::std::int32_t nameID, const ::DotNet::UnityEngine::Texture& value) const;
  private: static void (*CallSetFloat_D__nDm70ZmOnS4ff1jXmV2g)(void* thiz, ::std::int32_t nameID, float value, void** reinteropException);
  public: void SetFloat(::std::int32_t nameID, float value) const;
  private: static void (*CallSetVector_O_6hMsPoe8Mxh6B7ktm1dw)(void* thiz, ::std::int32_t nameID, const ::DotNet::UnityEngine::Vector4* value, void** reinteropException);
  public: void SetVector(::std::int32_t nameID, const ::DotNet::UnityEngine::Vector4& value) const;
  private: static void (*CallDisableKeyword_OjhTXlNYqXjpgz6Nd_41__A)(void* thiz, void* keyword, void** reinteropException);
  public: void DisableKeyword(const ::DotNet::System::String& keyword) const;
  private: static void (*CallEnableKeyword_OjhTXlNYqXjpgz6Nd_41__A)(void* thiz, void* keyword, void** reinteropException);
  public: void EnableKeyword(const ::DotNet::System::String& keyword) const;
  private: static void* (*CallGetTexture_FH4N7HzmeU2VNRINVzNxBQ)(void* thiz, ::std::int32_t nameID, void** reinteropException);
  public: ::DotNet::UnityEngine::Texture GetTexture(::std::int32_t nameID) const;
  private: static void (*CallSetTextureOffset_ZCDR2hJmAGOF0Xsc__aBBJA)(void* thiz, ::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2* value, void** reinteropException);
  public: void SetTextureOffset(::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2& value) const;
  private: static void (*CallSetTextureScale_ZCDR2hJmAGOF0Xsc__aBBJA)(void* thiz, ::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2* value, void** reinteropException);
  public: void SetTextureScale(::std::int32_t nameID, const ::DotNet::UnityEngine::Vector2& value) const;
  private: static void (*CallGetTexturePropertyNameIDs_HlbsadfaizcXlyyoqQEA3Q)(void* thiz, void* outNames, void** reinteropException);
  public: void GetTexturePropertyNameIDs(const ::DotNet::System::Collections::Generic::List1<::std::int32_t>& outNames) const;
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
  public: bool operator==(const Material& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const Material& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::UnityEngine


