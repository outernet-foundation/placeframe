#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <functional>

namespace DotNet::System {
class Object;
}
namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class MulticastDelegate;
}
namespace DotNet::System {
class Delegate;
}

namespace DotNet::System {

template <typename T0, typename T1>
class Func2;

template <> class Func2<::DotNet::System::Object, ::DotNet::System::Object> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Func2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Func2(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::MulticastDelegate() const;
  public: operator ::DotNet::System::Delegate() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallInvoke_lYA9p9IAgcAW1UlWV_LvhA)(void* thiz, void* arg, void** reinteropException);
  public: ::DotNet::System::Object Invoke(const ::DotNet::System::Object& arg) const;
  private: static ::std::uint8_t (*Callop_Equality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2);
  public: bool operator==(const ::DotNet::System::MulticastDelegate& rhs) const;
  public: bool operator==(const Func2& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2);
  public: bool operator!=(const ::DotNet::System::MulticastDelegate& rhs) const;
  public: bool operator!=(const Func2& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2);
  public: bool operator==(const ::DotNet::System::Delegate& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2);
  public: bool operator!=(const ::DotNet::System::Delegate& rhs) const;
  private: static void* (*CreateDelegate)(void* pCallbackFunction);
  public: using FunctionSignature = ::DotNet::System::Object (const ::DotNet::System::Object&);
  public: Func2(std::function<FunctionSignature> callback);
  private: static void* (*CombineDelegates)(void* thiz, void* rhs);
  private: static void* (*RemoveDelegate)(void* thiz, void* rhs);
  public: ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object> operator+(const ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>& rhs) const;
  public: ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object> operator-(const ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>& rhs) const;
  private: static void (*DisposeDelegate)(void* thiz);
  public: void Dispose();
};

} // namespace DotNet::System


