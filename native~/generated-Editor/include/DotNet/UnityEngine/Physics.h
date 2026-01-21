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

class Physics {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Physics(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Physics(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallBakeMesh_dUTFInDZC08B3wpYvm01lw)(::std::int32_t meshID, ::std::uint8_t convex, void** reinteropException);
  public: static void BakeMesh(::std::int32_t meshID, bool convex);
};

} // namespace DotNet::UnityEngine


