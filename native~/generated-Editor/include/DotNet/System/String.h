#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <string>

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
enum class StringComparison;
}
namespace DotNet::System {
template <typename T0> class Array1;
}

namespace DotNet::System {

class String {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit String(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: String(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static ::std::uint8_t (*Callop_Equality_46DLRq__QwpwCx8Uf20Cl7A)(void* a, void* b, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::System::String& a, const ::DotNet::System::String& b);
  public: bool operator==(const ::DotNet::System::String& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_46DLRq__QwpwCx8Uf20Cl7A)(void* a, void* b, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::System::String& a, const ::DotNet::System::String& b);
  public: bool operator!=(const ::DotNet::System::String& rhs) const;
  private: static ::std::uint8_t (*CallContains_GImL1A5rlEQAx14EidO2oA)(void* thiz, void* value, ::std::uint32_t comparisonType, void** reinteropException);
  public: bool Contains(const ::DotNet::System::String& value, ::DotNet::System::StringComparison comparisonType) const;
  private: static ::std::uint8_t (*CallEquals_46DLRq__QwpwCx8Uf20Cl7A)(void* a, void* b, void** reinteropException);
  public: static bool Equals(const ::DotNet::System::String& a, const ::DotNet::System::String& b);
  private: static ::std::uint8_t (*CallIsNullOrEmpty_ZOWEGUlscki07yVzH4i4ww)(void* value, void** reinteropException);
  public: static bool IsNullOrEmpty(const ::DotNet::System::String& value);
  private: static void* (*CallConcat_yq7nlytzIFp8a79slfH_mw)(void* arg0, void* arg1, void** reinteropException);
  public: static ::DotNet::System::String Concat(const ::DotNet::System::Object& arg0, const ::DotNet::System::Object& arg1);
  private: static void* (*CallConcat_OM9SoWVFMTHXvbepMyUchw)(void* str0, void* str1, void** reinteropException);
  public: static ::DotNet::System::String Concat(const ::DotNet::System::String& str0, const ::DotNet::System::String& str1);
  private: static void* (*CallJoin_ZMypEy2QfaUCbJCXuGMgzg)(void* separator, void* value, void** reinteropException);
  public: static ::DotNet::System::String Join(const ::DotNet::System::String& separator, const ::DotNet::System::Array1<::DotNet::System::String>& value);
  private: static ::std::uint8_t (*CallIsNullOrWhiteSpace_ZOWEGUlscki07yVzH4i4ww)(void* value, void** reinteropException);
  public: static bool IsNullOrWhiteSpace(const ::DotNet::System::String& value);
  public: String(const ::std::string& s);
  public: std::string ToStlString() const;
};

} // namespace DotNet::System


