#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "SelectIonTokenWindowImpl.h"

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
enum class IonTokenSource;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumIonServer;
}
namespace DotNet::System::Collections::Generic {
template <typename T0> class List1;
}
namespace DotNet::CesiumForUnity {
class SelectIonTokenWindow;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class SelectIonTokenWindow {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit SelectIonTokenWindow(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: SelectIonTokenWindow(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEditor::EditorWindow() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint32_t (*Property_get_tokenSource)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::IonTokenSource tokenSource() const;
  private: static void (*Property_set_tokenSource)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void tokenSource(::DotNet::CesiumForUnity::IonTokenSource value) const;
  private: static void* (*Property_get_createdTokenName)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String createdTokenName() const;
  private: static void (*Property_set_createdTokenName)(void* thiz, void* value, void** reinteropException);
  public: void createdTokenName(const ::DotNet::System::String& value) const;
  private: static ::std::int32_t (*Property_get_selectedExistingTokenIndex)(void* thiz, void** reinteropException);
  public: ::std::int32_t selectedExistingTokenIndex() const;
  private: static void (*Property_set_selectedExistingTokenIndex)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void selectedExistingTokenIndex(::std::int32_t value) const;
  private: static void* (*Property_get_specifiedToken)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String specifiedToken() const;
  private: static void (*Property_set_specifiedToken)(void* thiz, void* value, void** reinteropException);
  public: void specifiedToken(const ::DotNet::System::String& value) const;
  private: static void* (*CallGetDefaultNewTokenName_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: static ::DotNet::System::String GetDefaultNewTokenName();
  private: static void (*CallShowWindow_ouKG7YNdV4bUJcBV0W3dBA)(void* server, void** reinteropException);
  public: static void ShowWindow(const ::DotNet::CesiumForUnity::CesiumIonServer& server);
  private: static void* (*CallGetExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::List1<::DotNet::System::String> GetExistingTokenList() const;
  private: static void (*CallRefreshExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void RefreshExistingTokenList() const;
  private: static void* (*Field_get_currentWindow)(void** reinteropException);
  private: static void (*Field_set_currentWindow)(void* value, void** reinteropException);
  public: static ::DotNet::CesiumForUnity::SelectIonTokenWindow currentWindow();
  public: static void currentWindow(const ::DotNet::CesiumForUnity::SelectIonTokenWindow& value);
  private: static void* (*Field_get_server)(void* thiz, void** reinteropException);
  private: static void (*Field_set_server)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonServer server() const;
  public: void server(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const;
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
  public: bool operator==(const SelectIonTokenWindow& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const SelectIonTokenWindow& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::SelectIonTokenWindowImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


