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
namespace DotNet::UnityEditor {
class EditorWindow;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
class CesiumIonAsset;
}
namespace DotNet::CesiumForUnity {
class TokenTroubleshootingDetails;
}
namespace DotNet::CesiumForUnity {
class AssetTroubleshootingDetails;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class IonTokenTroubleshootingWindow {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit IonTokenTroubleshootingWindow(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: IonTokenTroubleshootingWindow(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEditor::EditorWindow() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_ionAsset)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonAsset ionAsset() const;
  private: static void (*Property_set_ionAsset)(void* thiz, void* value, void** reinteropException);
  public: void ionAsset(const ::DotNet::CesiumForUnity::CesiumIonAsset& value) const;
  private: static void* (*Property_get_assetTokenDetails)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::TokenTroubleshootingDetails assetTokenDetails() const;
  private: static void* (*Property_get_defaultTokenDetails)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::TokenTroubleshootingDetails defaultTokenDetails() const;
  private: static void* (*Property_get_assetDetails)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::AssetTroubleshootingDetails assetDetails() const;
  private: static void (*CallUseDefaultToken_qpX7eE7SvOg4KIeidX7yng)(void* asset, void** reinteropException);
  public: static void UseDefaultToken(const ::DotNet::CesiumForUnity::CesiumIonAsset& asset);
  private: static void (*CallClose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Close() const;
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
  public: bool operator==(const IonTokenTroubleshootingWindow& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const IonTokenTroubleshootingWindow& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::CesiumForUnity


