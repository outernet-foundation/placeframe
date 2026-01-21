#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class String;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::CesiumForUnity {

class CesiumCreditComponent {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumCreditComponent(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumCreditComponent(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_hnJK39H7_p9CsaJF5ySJ5Q)(void* text, void* link, ::std::int32_t imageId, void** reinteropException);
  public: CesiumCreditComponent(const ::DotNet::System::String& text, const ::DotNet::System::String& link, ::std::int32_t imageId);
  public: operator ::DotNet::System::Object() const;
};

} // namespace DotNet::CesiumForUnity


