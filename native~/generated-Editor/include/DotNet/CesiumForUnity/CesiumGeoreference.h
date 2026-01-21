#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumGeoreferenceImpl.h"

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
enum class CesiumGeoreferenceOriginPlacement;
}
namespace DotNet::CesiumForUnity {
enum class CesiumGeoreferenceOriginAuthority;
}
namespace DotNet::Unity::Mathematics {
struct double4x4;
}
namespace DotNet::CesiumForUnity {
class CesiumEllipsoid;
}
namespace DotNet::System {
class Action;
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
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class CesiumGeoreference {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumGeoreference(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumGeoreference(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEngine::MonoBehaviour() const;
  public: operator ::DotNet::UnityEngine::Behaviour() const;
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static double (*Property_get_longitude)(void* thiz, void** reinteropException);
  public: double longitude() const;
  private: static void (*Property_set_longitude)(void* thiz, double value, void** reinteropException);
  public: void longitude(double value) const;
  private: static double (*Property_get_latitude)(void* thiz, void** reinteropException);
  public: double latitude() const;
  private: static void (*Property_set_latitude)(void* thiz, double value, void** reinteropException);
  public: void latitude(double value) const;
  private: static double (*Property_get_height)(void* thiz, void** reinteropException);
  public: double height() const;
  private: static void (*Property_set_height)(void* thiz, double value, void** reinteropException);
  public: void height(double value) const;
  private: static double (*Property_get_ecefX)(void* thiz, void** reinteropException);
  public: double ecefX() const;
  private: static void (*Property_set_ecefX)(void* thiz, double value, void** reinteropException);
  public: void ecefX(double value) const;
  private: static double (*Property_get_ecefY)(void* thiz, void** reinteropException);
  public: double ecefY() const;
  private: static void (*Property_set_ecefY)(void* thiz, double value, void** reinteropException);
  public: void ecefY(double value) const;
  private: static double (*Property_get_ecefZ)(void* thiz, void** reinteropException);
  public: double ecefZ() const;
  private: static void (*Property_set_ecefZ)(void* thiz, double value, void** reinteropException);
  public: void ecefZ(double value) const;
  private: static ::std::uint32_t (*Property_get_originPlacement)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumGeoreferenceOriginPlacement originPlacement() const;
  private: static void (*Property_set_originPlacement)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void originPlacement(::DotNet::CesiumForUnity::CesiumGeoreferenceOriginPlacement value) const;
  private: static ::std::uint32_t (*Property_get_originAuthority)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumGeoreferenceOriginAuthority originAuthority() const;
  private: static void (*Property_set_originAuthority)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void originAuthority(::DotNet::CesiumForUnity::CesiumGeoreferenceOriginAuthority value) const;
  private: static double (*Property_get_scale)(void* thiz, void** reinteropException);
  public: double scale() const;
  private: static void (*Property_set_scale)(void* thiz, double value, void** reinteropException);
  public: void scale(double value) const;
  private: static void (*Property_get_ecefToLocalMatrix)(void* thiz, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException);
  public: ::DotNet::Unity::Mathematics::double4x4 ecefToLocalMatrix() const;
  private: static void* (*Property_get_ellipsoid)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumEllipsoid ellipsoid() const;
  private: static void (*Property_set_ellipsoid)(void* thiz, void* value, void** reinteropException);
  public: void ellipsoid(const ::DotNet::CesiumForUnity::CesiumEllipsoid& value) const;
  private: static void (*CallMoveOrigin_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void MoveOrigin() const;
  private: static void (*Calladd_changed_lHaT5LN6vSYwmLLE2__7bOw)(void* thiz, void* value, void** reinteropException);
  public: void add_changed(const ::DotNet::System::Action& value) const;
  private: static void (*Callremove_changed_lHaT5LN6vSYwmLLE2__7bOw)(void* thiz, void* value, void** reinteropException);
  public: void remove_changed(const ::DotNet::System::Action& value) const;
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
  public: bool operator==(const CesiumGeoreference& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumGeoreference& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumGeoreferenceImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


