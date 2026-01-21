#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumMetadataImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
class MonoBehaviour;
}
namespace DotNet::UnityEngine {
class Behaviour;
}
namespace DotNet::UnityEngine {
class Component;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
class CesiumFeature;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::UnityEngine {
class Coroutine;
}
namespace DotNet::System::Collections {
class IEnumerator;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class CesiumMetadata {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumMetadata(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumMetadata(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEngine::MonoBehaviour() const;
  public: operator ::DotNet::UnityEngine::Behaviour() const;
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallGetFeatures_5FygR9Vikuo7JxfnCBErUQ)(void* thiz, void* transform, ::std::int32_t triangleIndex, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumFeature> GetFeatures(const ::DotNet::UnityEngine::Transform& transform, ::std::int32_t triangleIndex) const;
  private: static void* (*CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException);
  public: ::DotNet::UnityEngine::Coroutine StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const;
  private: static ::std::uint8_t (*Property_get_enabled)(void* thiz, void** reinteropException);
  public: bool enabled() const;
  private: static void (*Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void enabled(bool value) const;
  private: static void* (*Property_get_gameObject)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::GameObject gameObject() const;
  private: static void* (*Property_get_transform)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform transform() const;
  public: template <typename T>
  T GetComponent() const;
  private: static void* (*CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException);
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
  public: bool operator==(const CesiumMetadata& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumMetadata& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumMetadataImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


