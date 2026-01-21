#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/int2.h>

namespace DotNet::Unity::Mathematics {
struct int2;
}
namespace DotNet::Unity::Mathematics {
struct int2x2;
}

namespace DotNet::Unity::Mathematics {

struct int2x2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_mnOQ_opjj2StriajDwrD9g)(const ::DotNet::Unity::Mathematics::int2* c0, const ::DotNet::Unity::Mathematics::int2* c1, ::DotNet::Unity::Mathematics::int2x2* pReturnValue, void** reinteropException);
  public: static int2x2 Construct(const ::DotNet::Unity::Mathematics::int2& c0, const ::DotNet::Unity::Mathematics::int2& c1);
  public: ::DotNet::Unity::Mathematics::int2 c0;
  public: ::DotNet::Unity::Mathematics::int2 c1;
};

} // namespace DotNet::Unity::Mathematics


