#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::CesiumForUnity {
class CesiumSampleHeightResult;
}
namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System::Threading::Tasks {
class Task;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::System::Threading::Tasks {

template <typename T0>
class Task1;

template <> class Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Task1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Task1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Threading::Tasks::Task() const;
  public: operator ::DotNet::System::Object() const;
};

} // namespace DotNet::System::Threading::Tasks


