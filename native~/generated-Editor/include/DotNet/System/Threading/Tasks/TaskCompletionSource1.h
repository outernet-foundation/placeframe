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
namespace DotNet::System {
class Object;
}
namespace DotNet::System::Threading::Tasks {
template <typename T0> class Task1;
}
namespace DotNet::System {
class Exception;
}

namespace DotNet::System::Threading::Tasks {

template <typename T0>
class TaskCompletionSource1;

template <> class TaskCompletionSource1<::DotNet::CesiumForUnity::CesiumSampleHeightResult> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit TaskCompletionSource1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: TaskCompletionSource1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: TaskCompletionSource1();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Task)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Threading::Tasks::Task1<::DotNet::CesiumForUnity::CesiumSampleHeightResult> Task() const;
  private: static void (*CallSetException_VrvSHSzTF_R2DRLTwid8jg)(void* thiz, void* exception, void** reinteropException);
  public: void SetException(const ::DotNet::System::Exception& exception) const;
  private: static void (*CallSetResult_DgnA9fh8lXZZ0ttkGvLh0w)(void* thiz, void* result, void** reinteropException);
  public: void SetResult(const ::DotNet::CesiumForUnity::CesiumSampleHeightResult& result) const;
};

} // namespace DotNet::System::Threading::Tasks


