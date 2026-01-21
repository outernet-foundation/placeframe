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
namespace DotNet::System::Threading::Tasks {
class Task;
}
namespace DotNet::System {
class Action;
}

namespace DotNet::System::Threading::Tasks {

class Task {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Task(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Task(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallRun_uG3jiSYLEmrwe0pJoPtxoA)(void* action, void** reinteropException);
  public: static ::DotNet::System::Threading::Tasks::Task Run(const ::DotNet::System::Action& action);
};

} // namespace DotNet::System::Threading::Tasks


