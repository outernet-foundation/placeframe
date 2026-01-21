#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/int3.h>

namespace DotNet::Unity::Mathematics {
struct int3;
}
namespace DotNet::Unity::Mathematics {
struct int3x3;
}

namespace DotNet::Unity::Mathematics {

struct int3x3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_A__Tj4TB5T_s22Xd4RW46Fg)(const ::DotNet::Unity::Mathematics::int3* c0, const ::DotNet::Unity::Mathematics::int3* c1, const ::DotNet::Unity::Mathematics::int3* c2, ::DotNet::Unity::Mathematics::int3x3* pReturnValue, void** reinteropException);
  public: static int3x3 Construct(const ::DotNet::Unity::Mathematics::int3& c0, const ::DotNet::Unity::Mathematics::int3& c1, const ::DotNet::Unity::Mathematics::int3& c2);
  public: ::DotNet::Unity::Mathematics::int3 c0;
  public: ::DotNet::Unity::Mathematics::int3 c1;
  public: ::DotNet::Unity::Mathematics::int3 c2;
};

} // namespace DotNet::Unity::Mathematics


