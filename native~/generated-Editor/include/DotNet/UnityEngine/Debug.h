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

class Debug {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Debug(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Debug(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallLog_FA05wu8x__otZNsgdHTnU9A)(void* message, void** reinteropException);
  public: static void Log(const ::DotNet::System::Object& message);
  private: static void (*CallLogWarning_FA05wu8x__otZNsgdHTnU9A)(void* message, void** reinteropException);
  public: static void LogWarning(const ::DotNet::System::Object& message);
  private: static void (*CallLogError_FA05wu8x__otZNsgdHTnU9A)(void* message, void** reinteropException);
  public: static void LogError(const ::DotNet::System::Object& message);
};

} // namespace DotNet::UnityEngine


