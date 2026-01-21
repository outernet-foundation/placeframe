#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::Unity::Collections {
enum class Allocator;
}
namespace DotNet::Unity::Collections {
enum class NativeArrayOptions;
}
namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Vector2;
}

namespace DotNet::Unity::Collections {

template <typename T0>
struct NativeArray1;

template <> struct NativeArray1<::std::uint8_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeArray1(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException);
  public: NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options);
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static ::std::uint8_t (*Callop_Equality___ZFbUbDYmnqRGnwegIjKPw)(void* left, void* right, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& right);
  public: bool operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality___ZFbUbDYmnqRGnwegIjKPw)(void* left, void* right, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& right);
  public: bool operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& rhs) const;
};

template <typename T0>
struct NativeArray1;

template <> struct NativeArray1<::DotNet::UnityEngine::Vector3> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeArray1(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: NativeArray1();
  private: static void* (*Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException);
  public: NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options);
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static ::std::uint8_t (*Callop_Equality_vrdbfdWf_jNnpc3OykEL7A)(void* left, void* right, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& right);
  public: bool operator==(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_vrdbfdWf_jNnpc3OykEL7A)(void* left, void* right, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& right);
  public: bool operator!=(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& rhs) const;
  private: static void (*CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Dispose() const;
};

template <typename T0>
struct NativeArray1;

template <> struct NativeArray1<::DotNet::UnityEngine::Vector2> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeArray1(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: NativeArray1();
  private: static void* (*Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException);
  public: NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options);
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static ::std::uint8_t (*Callop_Equality_upxAhiBTuli9tU8WNSSzEg)(void* left, void* right, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& right);
  public: bool operator==(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_upxAhiBTuli9tU8WNSSzEg)(void* left, void* right, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& left, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& right);
  public: bool operator!=(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& rhs) const;
  private: static void (*CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Dispose() const;
};

template <typename T0>
struct NativeArray1;

template <> struct NativeArray1<::std::int32_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeArray1(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: NativeArray1();
  private: static void* (*Construct_fyLz0cEPCtnsPNSt__omZwQ)(::std::int32_t length, ::std::uint32_t allocator, ::std::uint32_t options, void** reinteropException);
  public: NativeArray1(::std::int32_t length, ::DotNet::Unity::Collections::Allocator allocator, ::DotNet::Unity::Collections::NativeArrayOptions options);
  private: static ::std::uint8_t (*Callop_Equality_udAsXu_l5uh9odAsOsJXHQ)(void* left, void* right, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& right);
  public: bool operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_udAsXu_l5uh9odAsOsJXHQ)(void* left, void* right, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& right);
  public: bool operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& rhs) const;
  private: static void (*CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Dispose() const;
};

template <typename T0>
struct NativeArray1;

template <> struct NativeArray1<::std::uint16_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeArray1(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static ::std::uint8_t (*Callop_Equality_V583jKrqBJAPH29Lt9agWA)(void* left, void* right, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& right);
  public: bool operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_V583jKrqBJAPH29Lt9agWA)(void* left, void* right, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& right);
  public: bool operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& rhs) const;
};

template <typename T0>
struct NativeArray1;

template <> struct NativeArray1<::std::uint32_t> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeArray1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeArray1(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static ::std::uint8_t (*Callop_Equality_Mjak7jxj5GQBeCOOhOuHAw)(void* left, void* right, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& right);
  public: bool operator==(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_Mjak7jxj5GQBeCOOhOuHAw)(void* left, void* right, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& left, const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& right);
  public: bool operator!=(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& rhs) const;
};

} // namespace DotNet::Unity::Collections


