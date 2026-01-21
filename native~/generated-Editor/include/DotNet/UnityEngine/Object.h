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
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
template <typename T0> class Array1;
}

namespace DotNet::UnityEngine {

class Object {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Object(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Object(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
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
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: template <typename T>
  static ::DotNet::System::Array1<T> FindObjectsOfType();
  private: static void* (*CallFindObjectsOfType_0EgxpGTzCG1YTfWqwgLniw)(void** reinteropException);
  private: static void (*CallDestroyImmediate_c5oFMRh3nzKMIo8On83YBg)(void* obj, ::std::uint8_t allowDestroyingAssets, void** reinteropException);
  public: static void DestroyImmediate(const ::DotNet::UnityEngine::Object& obj, bool allowDestroyingAssets);
  private: static void (*CallDestroyImmediate_x7aQMuJcEpatC9689ghI4A)(void* obj, void** reinteropException);
  public: static void DestroyImmediate(const ::DotNet::UnityEngine::Object& obj);
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  public: template <typename T>
  static T Instantiate(const T& original);
  private: static void* (*CallInstantiate_zoaJbce7UThbChk6y9FLqQ)(void* original, void** reinteropException);
  private: static void (*CallDestroy_x7aQMuJcEpatC9689ghI4A)(void* obj, void** reinteropException);
  public: static void Destroy(const ::DotNet::UnityEngine::Object& obj);
  private: static void* (*CallInstantiate_FQyuyLH6iz8rpKkiJwlxBA)(void* original, void** reinteropException);
};

} // namespace DotNet::UnityEngine


