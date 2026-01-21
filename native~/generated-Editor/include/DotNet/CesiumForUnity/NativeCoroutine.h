#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
template <typename T0, typename T1> class Func2;
}
namespace DotNet::System::Collections {
class IEnumerator;
}

namespace DotNet::CesiumForUnity {

class NativeCoroutine {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit NativeCoroutine(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: NativeCoroutine(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_cIsazMJakk__Bsh3eD72HgQ)(void* callback, void** reinteropException);
  public: NativeCoroutine(const ::DotNet::System::Func2<::DotNet::System::Object, ::DotNet::System::Object>& callback);
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::IEnumerator GetEnumerator() const;
};

} // namespace DotNet::CesiumForUnity


