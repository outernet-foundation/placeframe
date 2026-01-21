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
namespace DotNet::UnityEngine {
class AsyncOperation;
}
namespace DotNet::System {
template <typename T0> class Action1;
}

namespace DotNet::UnityEngine {

class AsyncOperation {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit AsyncOperation(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: AsyncOperation(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void (*Calladd_completed_89b__Riirtgd1Q5mmRzPojA)(void* thiz, void* value, void** reinteropException);
  public: void add_completed(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& value) const;
  private: static void (*Callremove_completed_89b__Riirtgd1Q5mmRzPojA)(void* thiz, void* value, void** reinteropException);
  public: void remove_completed(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& value) const;
};

} // namespace DotNet::UnityEngine


