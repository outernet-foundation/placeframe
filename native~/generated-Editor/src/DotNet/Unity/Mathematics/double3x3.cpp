#include <DotNet/Unity/Mathematics/double3x3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::Unity::Mathematics {
struct double3x3;
}

namespace DotNet::Unity::Mathematics {

void (*double3x3::Construct_qgf8OQh32bnPxjj_codUtg)(const ::DotNet::Unity::Mathematics::double3* c0, const ::DotNet::Unity::Mathematics::double3* c1, const ::DotNet::Unity::Mathematics::double3* c2, ::DotNet::Unity::Mathematics::double3x3* pReturnValue, void** reinteropException) = nullptr;


double3x3 double3x3::Construct(const ::DotNet::Unity::Mathematics::double3& c0, const ::DotNet::Unity::Mathematics::double3& c1, const ::DotNet::Unity::Mathematics::double3& c2)
{
    void* reinteropException = nullptr;
    double3x3 result;
    Construct_qgf8OQh32bnPxjj_codUtg(&c0, &c1, &c2, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Unity::Mathematics::double3x3::Property_get_Item)(const ::DotNet::Unity::Mathematics::double3x3* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double3 double3x3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


